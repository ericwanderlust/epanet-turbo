#ifndef EPANET_BATCH_H
#define EPANET_BATCH_H
#include <stdint.h>
#ifdef _WIN32
#ifdef epanet2_EXPORTS
#define ENT_EXPORT __declspec(dllexport)
#else
#define ENT_EXPORT
#endif
#define ENT_CALL __stdcall
#else
#define ENT_EXPORT __attribute__((visibility("default")))
#define ENT_CALL
#endif
#ifdef __cplusplus
extern "C" {
#endif
/* Indices are EPANET's 1-based node or link indices. */
ENT_EXPORT int32_t ENT_CALL ENT_set_node_values(void *project, int32_t property,
    const int32_t *indices, const double *values, int32_t count);
ENT_EXPORT int32_t ENT_CALL ENT_set_link_values(void *project, int32_t property,
    const int32_t *indices, const double *values, int32_t count);
ENT_EXPORT int32_t ENT_CALL ENT_set_demand_multiplier(void *project, double factor);
#ifdef __cplusplus
}
#endif
#endif
