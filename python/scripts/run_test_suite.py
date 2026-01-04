#!/usr/bin/env python3
"""
测试套件编排和执行脚本

用法:
    python scripts/run_test_suite.py <suite_name> [options]

示例:
    python scripts/run_test_suite.py smoke
    python scripts/run_test_suite.py regression --parallel
    python scripts/run_test_suite.py all --workers=8
"""
import sys
import subprocess
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.markers import TEST_SUITES, MODULE_SUITES, get_suite_markers, get_suite_description
from tests.test_config import DEFAULT_WORKERS, REPORTS_DIR


def build_pytest_command(suite_name: str, parallel: bool = False, workers: int = None, 
                         coverage: bool = True, html_report: bool = True, 
                         json_report: bool = True, verbose: bool = True) -> list:
    """
    构建 pytest 命令
    
    Args:
        suite_name: 测试套件名称
        parallel: 是否并行执行
        workers: 并行工作进程数
        coverage: 是否生成覆盖率报告
        html_report: 是否生成HTML报告
        json_report: 是否生成JSON报告
        verbose: 是否详细输出
        
    Returns:
        pytest 命令列表
    """
    cmd = ["python", "-m", "pytest"]
    
    # 添加标记选择
    if suite_name == "all":
        # 执行所有测试，不添加标记过滤
        # 确保收集所有测试文件
        pass
    else:
        markers = get_suite_markers(suite_name)
        if markers:
            # 使用 OR 逻辑组合多个标记
            # 如果有多个标记，使用 or 连接；如果只有一个，直接使用
            if len(markers) > 1:
                marker_expr = " or ".join(markers)
            else:
                marker_expr = markers[0]
            cmd.extend(["-m", marker_expr])
        else:
            print(f"警告: 未知的测试套件 '{suite_name}'，将执行所有测试")
    
    # 并行执行
    if parallel:
        workers = workers or DEFAULT_WORKERS
        cmd.extend(["-n", str(workers)])
    
    # 确定报告文件名
    # 如果是模块测试套件，使用模块名称作为报告文件名
    # 如果是测试类型套件（smoke、regression等），使用套件名称
    if suite_name in MODULE_SUITES:
        # 模块测试：生成独立报告
        report_name = suite_name
    elif suite_name == "all":
        # 所有测试：使用统一报告
        report_name = "all"
    else:
        # 测试类型套件：使用套件名称
        report_name = suite_name
    
    # 覆盖率报告
    if coverage:
        if suite_name in MODULE_SUITES:
            # 模块测试：生成独立的覆盖率报告
            coverage_dir = f"reports/coverage_{report_name}"
        else:
            # 其他测试：使用统一覆盖率报告
            coverage_dir = "reports/coverage"
        cmd.extend([
            "--cov=app",
            f"--cov-report=html:{coverage_dir}",
            "--cov-report=term-missing"
        ])
    
    # HTML报告
    if html_report:
        if suite_name in MODULE_SUITES:
            # 模块测试：生成独立报告
            html_file = f"reports/{report_name}_report.html"
        else:
            # 其他测试：使用统一报告
            html_file = f"reports/{report_name}_report.html"
        cmd.extend([
            f"--html={html_file}",
            "--self-contained-html"
        ])
    
    # JSON报告
    if json_report:
        if suite_name in MODULE_SUITES:
            # 模块测试：生成独立报告
            json_file = f"reports/{report_name}_report.json"
        else:
            # 其他测试：使用统一报告
            json_file = f"reports/{report_name}_report.json"
        cmd.extend([
            "--json-report",
            f"--json-report-file={json_file}"
        ])
    
    # 详细输出
    if verbose:
        cmd.append("-v")
    
    return cmd


def run_test_suite(suite_name: str, **options) -> int:
    """
    运行指定的测试套件
    
    Args:
        suite_name: 测试套件名称
        **options: 其他选项
        
    Returns:
        退出码（0表示成功，非0表示失败）
    """
    # 显示套件信息
    description = get_suite_description(suite_name)
    print(f"\n{'='*60}")
    print(f"运行测试套件: {suite_name}")
    print(f"描述: {description}")
    if suite_name in TEST_SUITES:
        print(f"预计时间: {TEST_SUITES[suite_name].get('expected_time', '未知')}")
    print(f"{'='*60}\n")
    
    # 构建命令
    cmd = build_pytest_command(suite_name, **options)
    
    # 显示执行的命令
    print(f"执行命令: {' '.join(cmd)}\n")
    
    # 执行测试
    result = subprocess.run(cmd, cwd=project_root)
    
    # 显示结果
    print(f"\n{'='*60}")
    if result.returncode == 0:
        print(f"✅ 测试套件 '{suite_name}' 执行成功")
        if options.get('html_report', True):
            # 确定报告文件名
            if suite_name in MODULE_SUITES:
                report_name = suite_name
            elif suite_name == "all":
                report_name = "all"
            else:
                report_name = suite_name
            html_file = REPORTS_DIR / f"{report_name}_report.html"
            print(f"📊 HTML报告: {html_file}")
        if options.get('json_report', True):
            # 确定报告文件名
            if suite_name in MODULE_SUITES:
                report_name = suite_name
            elif suite_name == "all":
                report_name = "all"
            else:
                report_name = suite_name
            json_file = REPORTS_DIR / f"{report_name}_report.json"
            print(f"📋 JSON报告: {json_file}")
        if options.get('coverage', True):
            # 确定覆盖率报告目录
            if suite_name in MODULE_SUITES:
                coverage_dir = REPORTS_DIR / f"coverage_{suite_name}"
            else:
                coverage_dir = REPORTS_DIR / "coverage"
            print(f"📈 覆盖率报告: {coverage_dir / 'index.html'}")
    else:
        print(f"❌ 测试套件 '{suite_name}' 执行失败 (退出码: {result.returncode})")
    print(f"{'='*60}\n")
    
    return result.returncode


def list_available_suites():
    """列出所有可用的测试套件"""
    print("\n可用的测试套件:\n")
    
    print("测试类型套件:")
    for name, config in TEST_SUITES.items():
        print(f"  - {name:15} : {config['description']} ({config.get('expected_time', '未知时间')})")
    
    print("\n模块测试套件:")
    for name, config in MODULE_SUITES.items():
        print(f"  - {name:15} : {config['description']}")
    
    print("\n特殊套件:")
    print(f"  - {'all':15} : 执行所有测试")
    print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="测试套件编排和执行脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s smoke                    # 执行冒烟测试
  %(prog)s regression --parallel    # 并行执行回归测试
  %(prog)s api --workers=8          # 使用8个进程执行API测试
  %(prog)s all --no-coverage        # 执行所有测试，不生成覆盖率报告
  %(prog)s --list                   # 列出所有可用套件
        """
    )
    
    parser.add_argument(
        "suite",
        nargs="?",
        help="测试套件名称 (smoke, regression, api, integration, model, performance, store, user, setting, language, currency, auth, all)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有可用的测试套件"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="并行执行测试"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"并行工作进程数 (默认: {DEFAULT_WORKERS})"
    )
    
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="不生成覆盖率报告"
    )
    
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="不生成HTML报告"
    )
    
    parser.add_argument(
        "--no-json",
        action="store_true",
        help="不生成JSON报告"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="安静模式（不显示详细输出）"
    )
    
    args = parser.parse_args()
    
    # 列出可用套件
    if args.list:
        list_available_suites()
        return 0
    
    # 检查是否提供了套件名称
    if not args.suite:
        parser.print_help()
        print("\n错误: 必须指定测试套件名称")
        print("使用 --list 查看所有可用套件")
        return 1
    
    # 检查套件是否存在
    if args.suite not in TEST_SUITES and args.suite not in MODULE_SUITES and args.suite != "all":
        print(f"错误: 未知的测试套件 '{args.suite}'")
        print("使用 --list 查看所有可用套件")
        return 1
    
    # 运行测试套件
    options = {
        "parallel": args.parallel,
        "workers": args.workers,
        "coverage": not args.no_coverage,
        "html_report": not args.no_html,
        "json_report": not args.no_json,
        "verbose": not args.quiet
    }
    
    return run_test_suite(args.suite, **options)


if __name__ == "__main__":
    sys.exit(main())

