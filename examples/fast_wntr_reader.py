"""Opt-in binary results reader for WNTR 1.4.0.

The read method is adapted from WNTR 1.4.0's wntr.epanet.io.BinFile.
WNTR is copyright 2024 National Technology & Engineering Solutions of
Sandia, LLC (NTESS), distributed under the Revised BSD License; see
the accompanying WNTR license for the terms and disclaimer.
"""

import logging
import sys
import warnings

import numpy as np
import pandas as pd
import wntr
from wntr.epanet.io import BinFile
from wntr.epanet.util import EN, FlowUnits, HydParam, MassUnits, PressureUnits, QualParam, QualType, StatisticsType, to_si

logger = logging.getLogger(__name__)
sys_default_enc = sys.getdefaultencoding()


class FastBinFile(BinFile):
    """Read EPANET binary output while avoiding a large temporary MultiIndex."""

    def __init__(self, *args, **kwargs):
        if wntr.__version__ != "1.4.0":
            raise RuntimeError("FastBinFile is validated for WNTR 1.4.0")
        super().__init__(*args, **kwargs)

    def read(self, filename, convergence_error=False, darcy_weisbach=False, convert=True):
        """Read a binary file and create a results object.

        Parameters
        ----------
        filename : str
            An EPANET BIN output file
        convergence_error: bool (optional)
            If convergence_error is True, an error will be raised if the
            simulation does not converge. If convergence_error is False, partial results are returned,
            a warning will be issued, and results.error_code will be set to 0
            if the simulation does not converge.  Default = False.

        Returns
        -------
        object
            returns a WaterNetworkResults object
        """
        self.results = wntr.sim.SimulationResults()

        logger.debug('Read binary EPANET data from %s',filename)
        dt_str = 'u1'  #.format(self.idlen)
        with open(filename, 'rb') as fin:
            ftype = self.ftype
            idlen = self.idlen
            logger.debug('... read prolog information ...')
            prolog = np.fromfile(fin, dtype=np.int32, count=15)
            magic1 = prolog[0]
            version = prolog[1]
            nnodes = prolog[2]
            ntanks = prolog[3]
            nlinks = prolog[4]
            npumps = prolog[5]
            nvalve = prolog[6]
            wqopt = QualType(prolog[7])
            srctrace = prolog[8]
            flowunits = FlowUnits(prolog[9])
            presunits = PressureUnits(prolog[10])
            statsflag = StatisticsType(prolog[11])
            reportstart = prolog[12]
            reportstep = prolog[13]
            duration = prolog[14]
            logger.debug('EPANET/Toolkit version %d',version)
            logger.debug('Nodes: %d; Tanks/Resrv: %d Links: %d; Pumps: %d; Valves: %d',
                         nnodes, ntanks, nlinks, npumps, nvalve)
            logger.debug('WQ opt: %s; Trace Node: %s; Flow Units %s; Pressure Units %s',
                         wqopt, srctrace, flowunits, presunits)
            logger.debug('Statistics: %s; Report Start %d, step %d; Duration=%d sec',
                         statsflag, reportstart, reportstep, duration)

            np.fromfile(fin, dtype=np.uint8, count=240)
            inpfile = np.fromfile(fin, dtype=np.uint8, count=260)
            rptfile = np.fromfile(fin, dtype=np.uint8, count=260)
            chemical = bytes(np.fromfile(fin, dtype=dt_str, count=self.idlen)[:]).decode(sys_default_enc)
            wqunits = bytes(np.fromfile(fin, dtype=dt_str, count=self.idlen)[:]).decode(sys_default_enc)
            mass = wqunits.split('/',1)[0]
            if mass in ['mg', 'ug', u'mg', u'ug']:
                massunits = MassUnits[mass]
            else:
                massunits = MassUnits.mg
            self.flow_units = flowunits
            self.pres_units = presunits
            self.quality_type = wqopt
            self.mass_units = massunits
            self.num_nodes = nnodes
            self.num_tanks = ntanks
            self.num_links = nlinks
            self.num_pumps = npumps
            self.num_valves = nvalve
            self.report_start = reportstart
            self.report_step = reportstep
            self.duration = duration
            self.chemical = chemical
            self.chem_units = wqunits
            self.inp_file = inpfile
            self.report_file = rptfile
            nodenames = []
            linknames = []
            raw_names = np.fromfile(fin, dtype=np.dtype('S%d' % idlen), count=nnodes+nlinks)
            names = [bytes(name).decode(sys_default_enc).replace('\x00', '') for name in raw_names]
            nodenames = names[:nnodes]
            linknames = names[nnodes:]
            self.node_names = np.array(nodenames)
            self.link_names = np.array(linknames)
            linkstart = np.array(np.fromfile(fin, dtype=np.int32, count=nlinks), dtype=int)
            linkend = np.array(np.fromfile(fin, dtype=np.int32, count=nlinks), dtype=int)
            linktype = np.fromfile(fin, dtype=np.int32, count=nlinks)
            tankidxs = np.fromfile(fin, dtype=np.int32, count=ntanks)
            tankarea = np.fromfile(fin, dtype=np.dtype(ftype), count=ntanks)
            elevation = np.fromfile(fin, dtype=np.dtype(ftype), count=nnodes)
            linklen = np.fromfile(fin, dtype=np.dtype(ftype), count=nlinks)
            diameter = np.fromfile(fin, dtype=np.dtype(ftype), count=nlinks)

            logger.debug('... read energy data ...')
            for i in range(npumps):
                pidx = int(np.fromfile(fin,dtype=np.int32, count=1)[0])
                energy = np.fromfile(fin, dtype=np.dtype(ftype), count=6)
                self.save_energy_line(pidx, linknames[pidx-1], energy)
            peakenergy = np.fromfile(fin, dtype=np.dtype(ftype), count=1)
            self.peak_energy = peakenergy

            logger.debug('... read EP simulation data ...')
            reporttimes = np.arange(reportstart, duration+reportstep-(duration%reportstep), reportstep)
            nrptsteps = len(reporttimes)
            statsN = nrptsteps
            if statsflag in [StatisticsType.Maximum, StatisticsType.Minimum, StatisticsType.Range]:
                nrptsteps = 1
                reporttimes = [reportstart + reportstep]
            self.num_periods = nrptsteps
            self.report_times = reporttimes



            try:
                data = np.fromfile(fin, dtype = np.dtype(ftype), count = (4*nnodes+8*nlinks)*nrptsteps)
            except Exception as e:
                logger.exception('Failed to process file: %s', e)

            N = int(np.floor(len(data)/(4*nnodes+8*nlinks)))
            if N < nrptsteps:
                t = reporttimes[N]
                if convergence_error:
                    logger.error('Simulation did not converge at time ' + self._get_time(t) + '.')
                    raise RuntimeError('Simulation did not converge at time ' + self._get_time(t) + '.')
                else:
                    data = data[0:N*(4*nnodes+8*nlinks)]
                    data = np.reshape(data, (N, (4*nnodes+8*nlinks)))
                    reporttimes = reporttimes[0:N]
                    warnings.warn('Simulation did not converge at time ' + self._get_time(t) + '.')
                    self.results.error_code = wntr.sim.results.ResultsStatus.error
            else:
                data = np.reshape(data, (nrptsteps, (4*nnodes+8*nlinks)))
                self.results.error_code = None

            df = {}
            offset = 0
            node_fields = ('demand', 'head', 'pressure', 'quality')
            link_fields = ('flow', 'velocity', 'headloss', 'linkquality', 'linkstatus', 'linksetting', 'reactionrate', 'frictionfactor')
            for name, count, names in ([(name, nnodes, nodenames) for name in node_fields] +
                                       [(name, nlinks, linknames) for name in link_fields]):
                df[name] = pd.DataFrame(data[:, offset:offset+count], index=reporttimes,
                                        columns=pd.Index(names, name='name'))
                offset += count

            self.results.node = {}
            self.results.link = {}
            self.results.network_name = self.inp_file

            if convert:
                self.results.node['demand'] = HydParam.Demand._to_si(self.flow_units, df['demand'])
                self.results.node['head'] = HydParam.HydraulicHead._to_si(self.flow_units, df['head'])
                self.results.node['pressure'] = HydParam.Pressure._to_si(self.flow_units, df['pressure'])

                if self.quality_type is QualType.Chem:
                    self.results.node['quality'] = QualParam.Concentration._to_si(self.flow_units, df['quality'], mass_units=self.mass_units)
                    self.results.link['quality'] = QualParam.Concentration._to_si(self.flow_units, df['linkquality'], mass_units=self.mass_units)
                elif self.quality_type is QualType.Age:
                    self.results.node['quality'] = QualParam.WaterAge._to_si(self.flow_units, df['quality'], mass_units=self.mass_units)
                    self.results.link['quality'] = QualParam.WaterAge._to_si(self.flow_units, df['linkquality'], mass_units=self.mass_units)
                else:
                    self.results.node['quality'] = df['quality']
                    self.results.link['quality'] = df['linkquality']

                self.results.link['flowrate'] = HydParam.Flow._to_si(self.flow_units, df['flow'])
                self.results.link['velocity'] = HydParam.Velocity._to_si(self.flow_units, df['velocity'])

                headloss = np.array(df['headloss'])
                headloss[:, linktype < 2] = to_si(self.flow_units, headloss[:, linktype < 2], HydParam.HeadLoss) # Pipe or CV
                headloss[:, linktype >= 2] = to_si(self.flow_units, headloss[:, linktype >= 2], HydParam.Length) # Pump or Valve
                self.results.link["headloss"] = pd.DataFrame(data=headloss, columns=linknames, index=reporttimes)

                status = np.array(df['linkstatus'])
                if self.convert_status:
                    status[status <= 2] = 0
                    status[status == 3] = 1
                    status[status >= 5] = 1
                    status[status == 4] = 2
                self.results.link['status'] = pd.DataFrame(data=status, columns=linknames, index=reporttimes)

                setting = np.array(df['linksetting'])
                setting[:, linktype == EN.PIPE] = to_si(self.flow_units, setting[:, linktype == EN.PIPE], HydParam.RoughnessCoeff,
                                                darcy_weisbach=darcy_weisbach)
                setting[:, linktype == EN.PRV] = to_si(self.flow_units, setting[:, linktype == EN.PRV], HydParam.Pressure)
                setting[:, linktype == EN.PSV] = to_si(self.flow_units, setting[:, linktype == EN.PSV], HydParam.Pressure)
                setting[:, linktype == EN.PBV] = to_si(self.flow_units, setting[:, linktype == EN.PBV], HydParam.Pressure)
                setting[:, linktype == EN.FCV] = to_si(self.flow_units, setting[:, linktype == EN.FCV], HydParam.Flow)
                self.results.link['setting'] = pd.DataFrame(data=setting, columns=linknames, index=reporttimes)

                self.results.link['friction_factor'] = df['frictionfactor']
                self.results.link['reaction_rate'] = QualParam.ReactionRate._to_si(self.flow_units, df['reactionrate'],self.mass_units)
            else:
                self.results.node['demand'] = df['demand']
                self.results.node['head'] = df['head']
                self.results.node['pressure'] = df['pressure']
                self.results.node['quality'] = df['quality']

                self.results.link['flowrate'] = df['flow']
                self.results.link['headloss'] = df['headloss']
                self.results.link['velocity'] = df['velocity']
                self.results.link['quality'] = df['linkquality']
                self.results.link['status'] = df['linkstatus']
                self.results.link['setting'] = df['linksetting']
                self.results.link['friction_factor'] = df['frictionfactor']
                self.results.link['reaction_rate'] = df['reactionrate']

            logger.debug('... read epilog ...')
            averages = np.fromfile(fin, dtype=np.dtype(ftype), count=4)
            self.averages = averages
            np.fromfile(fin, dtype=np.int32, count=1)
            warnflag = np.fromfile(fin, dtype=np.int32, count=1)
            magic2 = np.fromfile(fin, dtype=np.int32, count=1)
            if magic1 != magic2:
                logger.critical('The magic number did not match -- binary incomplete or incorrectly read. If you believe this file IS complete, please try a different float type. Current type is "%s"',ftype)
            if warnflag != 0:
                logger.warning('Warnings were issued during simulation')
        self.finalize_save(magic1==magic2, warnflag)

        return self.results
