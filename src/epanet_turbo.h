/**
 * EPANET-Turbo Batch Setter API
 *
 * 高性能批量参数设置接口，减少 Python→DLL 调用次数。
 *
 * Copyright (c) 2026 ES (Serein)
 *
 * ABI 设计原则：
 * 1. 使用显式位宽类型 (int32_t, double)
 * 2. 统一 __cdecl calling convention
 * 3. indices 使用 EPANET 内部 1-based 索引
 * 4. 返回 EPANET 错误码 (0=成功)
 */

#ifndef EPANET_TURBO_H
#define EPANET_TURBO_H

#include "epanet_turbo_export.h"
#include <stdint.h>


// Unified Export Macro
// API handles export/import/visibility
// CALL handles calling convention (__stdcall)

#ifndef API
#ifdef _WIN32
#define API EPNT_API
#else
#define API EPNT_API
#endif
#endif

#ifndef CALL
#ifdef _WIN32
#define CALL __stdcall
#else
#define CALL
#endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

/**
 * 获取 EPANET-Turbo 版本号
 * @return 版本号 (例如 110 表示 v1.1.0)
 */
API int32_t CALL ENT_version(void);

/**
 * 批量设置节点属性
 *
 * @param ph       EN_Project 句柄
 * @param prop     属性代码 (EN_BASEDEMAND=1, EN_ELEVATION=0, 等)
 * @param indices  节点索引数组 (1-based, 与 EN_getnodeid 一致)
 * @param values   值数组
 * @param n        数组长度
 * @return         0=成功, 其他=第一个遇到的 EPANET 错误码
 */
API int32_t CALL ENT_set_node_values(void *ph, int32_t prop,
                                     const int32_t *indices,
                                     const double *values, int32_t n);

/**
 * 批量设置管段属性
 *
 * @param ph       EN_Project 句柄
 * @param prop     属性代码 (EN_INITSTATUS=11, EN_INITSETTING=10, 等)
 * @param indices  管段索引数组 (1-based)
 * @param values   值数组
 * @param n        数组长度
 * @return         0=成功, 其他=EPANET 错误码
 */
API int32_t CALL ENT_set_link_values(void *ph, int32_t prop,
                                     const int32_t *indices,
                                     const double *values, int32_t n);

/**
 * 全网需水量乘法器 (高频场景优化)
 *
 * 使用 EN_OPTION_DEMANDMULT 实现 O(1) 时间复杂度
 *
 * @param ph       EN_Project 句柄
 * @param factor   乘法因子
 * @return         0=成功
 */
API int32_t CALL ENT_set_demand_multiplier(void *ph, double factor);

/**
 * 性能剖析结构体
 */
typedef struct {
  double total;
  double assemble;
  double linear_solve;
  double headloss;
  double convergence;
  double controls;
  double rules_time;
  double simple_controls_time;
  int32_t step_count;
  int32_t iter_count;

  // Rules counters
  int32_t rules_eval_count;
  int32_t rules_fire_count;
  int32_t rules_skip_count;

  // Simple controls counters
  int32_t simple_controls_eval_count;
  int32_t simple_controls_fire_count;
  int32_t simple_controls_skip_count;
} ENT_ProfileStats;

/**
 * 获取性能剖析数据
 */
API int32_t CALL ENT_get_profile(void *ph, ENT_ProfileStats *out);

/**
 * M5 Identity & Control
 */
API const char *CALL ENT_engine_id(void);
API void CALL ENT_set_num_threads(int n);

/**
 * 调试规则信息
 */
API int32_t CALL ENT_debug_rule_info(void *ph, int32_t rule_index,
                                     int32_t *is_time_only,
                                     int64_t *next_eval_time);

#ifdef __cplusplus
}
#endif

#endif // EPANET_TURBO_H
