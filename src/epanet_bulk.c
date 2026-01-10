#include "epanet_bulk.h"
#include <string.h>

API int EN_get_counts(void* ph, int* n_nodes, int* n_links)
{
    int err = 0;
    int v = 0;

#ifdef EPANET_USE_GLOBAL_API
    if (n_nodes != NULL)
    {
        err = EN_getcount(EN_NODECOUNT, &v);
        if (err != 0)
        {
            return err;
        }
        *n_nodes = v;
    }
    if (n_links != NULL)
    {
        err = EN_getcount(EN_LINKCOUNT, &v);
        if (err != 0)
        {
            return err;
        }
        *n_links = v;
    }
#else
    if (n_nodes != NULL)
    {
        err = EN_getcount(ph, EN_NODECOUNT, &v);
        if (err != 0)
        {
            return err;
        }
        *n_nodes = v;
    }
    if (n_links != NULL)
    {
        err = EN_getcount(ph, EN_LINKCOUNT, &v);
        if (err != 0)
        {
            return err;
        }
        *n_links = v;
    }
#endif
    return 0;
}

API int EN_get_all_pressures(void* ph, int n_nodes, int pressureCode, double* out)
{
    int actual = 0;
    int err = 0;
    int i = 0;
    double value = 0.0;

    if (out == NULL || n_nodes <= 0)
    {
        return 202;
    }

    err = EN_get_counts(ph, &actual, NULL);
    if (err != 0)
    {
        return err;
    }
    if (n_nodes < actual)
    {
        return 202;
    }

#ifdef EPANET_USE_GLOBAL_API
    for (i = 1; i <= actual; ++i)
    {
        err = EN_getnodevalue(i, pressureCode, &value);
        if (err != 0)
        {
            return err;
        }
        out[i - 1] = value;
    }
#else
    for (i = 1; i <= actual; ++i)
    {
        err = EN_getnodevalue(ph, i, pressureCode, &value);
        if (err != 0)
        {
            return err;
        }
        out[i - 1] = value;
    }
#endif

    if (n_nodes > actual)
    {
        memset(out + actual, 0, (size_t)(n_nodes - actual) * sizeof(double));
    }

    return 0;
}

API int EN_get_all_flows(void* ph, int n_links, int flowCode, double* out)
{
    int actual = 0;
    int err = 0;
    int i = 0;
    double value = 0.0;

    if (out == NULL || n_links <= 0)
    {
        return 202;
    }

    err = EN_get_counts(ph, NULL, &actual);
    if (err != 0)
    {
        return err;
    }
    if (n_links < actual)
    {
        return 202;
    }

#ifdef EPANET_USE_GLOBAL_API
    for (i = 1; i <= actual; ++i)
    {
        err = EN_getlinkvalue(i, flowCode, &value);
        if (err != 0)
        {
            return err;
        }
        out[i - 1] = value;
    }
#else
    for (i = 1; i <= actual; ++i)
    {
        err = EN_getlinkvalue(ph, i, flowCode, &value);
        if (err != 0)
        {
            return err;
        }
        out[i - 1] = value;
    }
#endif

    if (n_links > actual)
    {
        memset(out + actual, 0, (size_t)(n_links - actual) * sizeof(double));
    }

    return 0;
}

