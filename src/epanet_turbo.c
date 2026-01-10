/**
 * EPANET-Turbo Batch Setter 实现
 *
 * Copyright (c) 2026 ES (Serein)
 */

#ifdef _OPENMP
#include <omp.h>
#endif

#include "epanet2_2.h"
#include "epanet_turbo.h"


// --- M5 Identity & Control ---

API const char *CALL ENT_engine_id(void) {
#if defined(EPNT_OPENMP) || defined(_OPENMP)
  return "Turbo-OpenMP";
#elif defined(EPNT_SERIAL)
  return "Turbo-Serial";
#else
  return "Turbo-Unknown";
#endif
}

API void CALL ENT_set_num_threads(int n) {
#if defined(EPNT_OPENMP) || defined(_OPENMP)
  if (n > 0) {
    omp_set_num_threads(n);
  }
#else
  // No-op for serial
  (void)n;
#endif
}

/* 版本号: 110 = v1.1.0 */
API int32_t CALL ENT_version(void) { return 110; }

/**
 * 批量设置节点属性
 *
 * 内部循环调用 EN_setnodevalue，将 Python 端数万次调用
 * 合并为一次跨语言调用。
 */
API int32_t CALL ENT_set_node_values(void *ph, int32_t prop,
                                     const int32_t *indices,
                                     const double *values, int32_t n) {
  int32_t err = 0;
  int32_t i;

  if (ph == NULL || indices == NULL || values == NULL || n <= 0) {
    return 202; /* EN_INVALIDPARAM */
  }

  for (i = 0; i < n; ++i) {
    err = EN_setnodevalue(ph, indices[i], prop, values[i]);
    if (err != 0) {
      return err; /* 返回第一个错误 */
    }
  }

  return 0;
}

/**
 * 批量设置管段属性
 */
API int32_t CALL ENT_set_link_values(void *ph, int32_t prop,
                                     const int32_t *indices,
                                     const double *values, int32_t n) {
  int32_t err = 0;
  int32_t i;

  if (ph == NULL || indices == NULL || values == NULL || n <= 0) {
    return 202;
  }

  for (i = 0; i < n; ++i) {
    err = EN_setlinkvalue(ph, indices[i], prop, values[i]);
    if (err != 0) {
      return err;
    }
  }

  return 0;
}

/**
 * 全网需水量乘法器
 *
 * 使用 EN_setoption(EN_DEMANDMULT) 实现 O(1) 时间复杂度。
 * 注意：EN_DEMANDMULT = 13 (在 epanet2_enums.h 中定义)
 */
API int32_t CALL ENT_set_demand_multiplier(void *ph, double factor) {
  if (ph == NULL) {
    return 202;
  }

  /* EN_DEMANDMULT = 13 */
  return EN_setoption(ph, 13, factor);
}
