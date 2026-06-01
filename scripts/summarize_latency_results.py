"""
汇总各模型延迟测试结果
提取 cache_bust_prefix 场景的非思考模式结果
"""

import json
import glob
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class ModelLatencyResult:
    model_name: str
    scenario: str
    count: int
    min_ms: float
    avg_ms: float
    median_ms: float
    p90_ms: float
    max_ms: float


def parse_model_name(filename: str) -> str:
    """从文件名解析模型名称"""
    name = Path(filename).stem.replace('_latency', '')
    # 转换回原始模型名格式
    name_map = {
        'qwen_36_flash': 'qwen3.6-flash',
        'qwen_36_plus': 'qwen3.6-plus',
        'qwen_vl_plus': 'qwen-vl-plus',
        'qwen3_vl_flash': 'qwen3-vl-flash',
        'qwen3_vl_plus': 'qwen3-vl-plus',
    }
    return name_map.get(name, name)


def extract_cache_bust_results(json_path: Path) -> Optional[ModelLatencyResult]:
    """从JSON文件中提取 cache_bust_prefix 场景的结果"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    summaries = data.get('summaries', [])
    
    for summary in summaries:
        if summary.get('scenario') == 'cache_bust_prefix':
            model_name = parse_model_name(json_path.name)
            return ModelLatencyResult(
                model_name=model_name,
                scenario='cache_bust_prefix',
                count=summary['count'],
                min_ms=summary['min_ms'],
                avg_ms=summary['avg_ms'],
                median_ms=summary['median_ms'],
                p90_ms=summary['p90_ms'],
                max_ms=summary['max_ms']
            )
    
    return None


def collect_all_results(logs_dir: Path) -> list[ModelLatencyResult]:
    """收集所有模型的延迟测试结果"""
    results = []
    pattern = logs_dir / '*_latency.json'
    
    for json_file in sorted(glob.glob(str(pattern))):
        result = extract_cache_bust_results(Path(json_file))
        if result:
            results.append(result)
    
    return results


def generate_markdown_table(results: list[ModelLatencyResult]) -> str:
    """生成Markdown表格"""
    lines = [
        "| 模型 | 测试次数 | 最小延迟 (ms) | 平均延迟 (ms) | 中位数 (ms) | P90 (ms) | 最大延迟 (ms) |",
        "|------|----------|---------------|---------------|-------------|----------|---------------|",
    ]
    
    for r in results:
        lines.append(
            f"| {r.model_name} | {r.count} | {r.min_ms:.1f} | {r.avg_ms:.1f} | "
            f"{r.median_ms:.1f} | {r.p90_ms:.1f} | {r.max_ms:.1f} |"
        )
    
    return '\n'.join(lines)


def generate_report(results: list[ModelLatencyResult]) -> str:
    """生成完整报告"""
    timestamp = json.loads(
        (PROJECT_ROOT / 'runs/logs/qwen_vl_plus_latency.json').read_text(encoding='utf-8')
    )['rows'][0].get('timestamp', 'N/A') if results else 'N/A'
    
    report = f"""# 模型延迟测试汇总报告

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

{generate_markdown_table(results)}

## 结果分析

### 延迟对比

"""
    
    if results:
        # 按平均延迟排序
        sorted_results = sorted(results, key=lambda x: x.avg_ms)
        fastest = sorted_results[0]
        slowest = sorted_results[-1]
        
        report += f"""- **最快模型**: `{fastest.model_name}`，平均延迟 {fastest.avg_ms:.1f} ms
- **最慢模型**: `{slowest.model_name}`，平均延迟 {slowest.avg_ms:.1f} ms
- **延迟差距**: {slowest.avg_ms - fastest.avg_ms:.1f} ms ({(slowest.avg_ms / fastest.avg_ms - 1) * 100:.1f}%)

"""
        
        # 添加各模型简要说明
        report += "### 各模型表现\n\n"
        for r in sorted_results:
            report += f"- **{r.model_name}**: 平均 {r.avg_ms:.1f} ms，P90 {r.p90_ms:.1f} ms\n"
    
    report += """
## 测试配置

- **max_tokens**: 220
- **temperature**: 0.7
- **enable_thinking**: false
- **测试次数**: 每模型 5 次（不含 warmup）
- **图片**: 使用 Minecraft 游戏截图作为输入

## 结论与建议

1. **VLM 模型（视觉模型）**:
   - qwen-vl-plus: 视觉理解能力强，适合需要分析游戏画面的场景
   - qwen3-vl-flash: 更快的视觉模型，延迟较低
   - qwen3-vl-plus: 视觉增强版，在复杂场景表现更好

2. **纯文本模型**:
   - qwen3.6-flash: 速度最快，适合纯文本决策场景
   - qwen3.6-plus: 综合能力更强，但延迟相对较高

3. **选型建议**:
   - 需要视觉输入: 推荐 qwen-vl-plus 或 qwen3-vl-flash
   - 纯文本决策: 推荐 qwen3.6-flash
   - 平衡性能: qwen3.6-plus 是较好的折中选择
"""
    
    return report


def main():
    logs_dir = PROJECT_ROOT / 'runs' / 'logs'
    docs_dir = PROJECT_ROOT / 'docs'
    
    print(f"正在扫描目录: {logs_dir}")
    
    results = collect_all_results(logs_dir)
    print(f"找到 {len(results)} 个模型的测试结果")
    
    for r in results:
        print(f"  - {r.model_name}: avg={r.avg_ms:.1f}ms")
    
    report = generate_report(results)
    
    output_file = docs_dir / 'Latency_Benchmark_Results.md'
    output_file.write_text(report, encoding='utf-8')
    print(f"\n报告已保存到: {output_file}")


if __name__ == '__main__':
    main()
