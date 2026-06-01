<!--
 * @Author: scofiedluo scofiedluo@gmail.com
 * @Date: 2026-06-01 17:02:27
 * @LastEditors: scofiedluo scofiedluo@gmail.com
 * @LastEditTime: 2026-06-01 17:09:14
 * @FilePath: \vlm-minecraft-agent\docs\Latency_Benchmark_Results.md
 * @Description: 
 * 
 * Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
-->
# 模型延迟测试汇总报告

> 生成时间: 2026-06-01
> 测试场景: `cache_bust_prefix`（非缓存场景，模拟真实使用情况）
> 思考模式: 关闭（非思考模式）

## 测试说明

- **测试方法**: 每次请求在 system prompt 前添加随机 nonce，确保 prefix cache 失效
- **测试目的**: 模拟实际使用中的无缓存场景，获取真实的端到端延迟
- **测试指标**: 
  - 最小/最大延迟：单次请求的最快/最慢响应时间
  - 平均延迟：所有请求的平均响应时间
  - 中位数：50% 请求在此时间内完成
  - P90：90% 请求在此时间内完成

## 测试结果汇总

| 模型 | 测试次数 | 最小延迟 (ms) | 平均延迟 (ms) | 中位数 (ms) | P90 (ms) | 最大延迟 (ms) |
|------|----------|---------------|---------------|-------------|----------|---------------|
| qwen3-vl-flash | 5 | 1820.4 | 2219.6 | 2127.9 | 2920.8 | 2920.8 |
| qwen3-vl-plus | 5 | 4963.8 | 5728.7 | 5326.8 | 7507.0 | 7507.0 |
| qwen3.6-flash | 5 | 1077.3 | 1164.9 | 1139.6 | 1275.2 | 1275.2 |
| qwen3.6-plus | 5 | 5460.3 | 7001.9 | 7177.3 | 9396.7 | 9396.7 |
| qwen-vl-plus | 5 | 2474.1 | 5012.3 | 5859.5 | 8030.8 | 8030.8 |

## 结果分析

### 延迟对比

- **最快模型**: `qwen3.6-flash`，平均延迟 1164.9 ms
- **最慢模型**: `qwen3.6-plus`，平均延迟 7001.9 ms
- **延迟差距**: 5837.0 ms (501.1%)

### 各模型表现

- **qwen3.6-flash**: 平均 1164.9 ms，P90 1275.2 ms
- **qwen3-vl-flash**: 平均 2219.6 ms，P90 2920.8 ms
- **qwen-vl-plus**: 平均 5012.3 ms，P90 8030.8 ms
- **qwen3-vl-plus**: 平均 5728.7 ms，P90 7507.0 ms
- **qwen3.6-plus**: 平均 7001.9 ms，P90 9396.7 ms

## 测试配置

- **max_tokens**: 512
- **temperature**: 0.7
- **enable_thinking**: false
- **测试次数**: 每模型 5 次（不含 warmup）
- **图片**: 使用 Minecraft 游戏截图作为输入

## 结论与建议

1. **VLM 模型（视觉模型）**:
   - qwen-vl-plus: 视觉理解能力强，适合需要分析游戏画面的场景
   - qwen3-vl-flash: 更快的视觉模型，延迟较低
   - qwen3-vl-plus: 视觉增强版，在复杂场景表现更好

2. **混合模型**:
   - qwen3.6-flash: 速度最快，适合纯文本决策场景
   - qwen3.6-plus: 综合能力更强，但延迟相对较高

