#pragma once
#ifdef __cplusplus
extern "C" {
#endif

#include "epanet_turbo_export.h"
#define API EPNT_API

#ifdef EPANET_USE_GLOBAL_API
#include "epanet2.h"
#else
#include "epanet2_2.h"
#endif

/* Helper note: return 202 when the caller supplies a null pointer or undersized
 * buffer. */
API int EN_get_counts(void *ph, int *n_nodes, int *n_links);

/* Bulk extraction helpers
   - ph: pass EN_Project for the 2.3 project API; define EPANET_USE_GLOBAL_API
   for the 2.2 global API
   - n_nodes/n_links: capacity of the caller-provided buffer (must be >= actual
   count) or 202 is returned
   - pressureCode/flowCode: EN_PRESSURE, EN_FLOW, etc.
   - out: double-precision array that receives values; unused slots are zeroed
*/
API int EN_get_all_pressures(void *ph, int n_nodes, int pressureCode,
                             double *out);
API int EN_get_all_flows(void *ph, int n_links, int flowCode, double *out);

#ifdef __cplusplus
}
#endif
