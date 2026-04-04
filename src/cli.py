"""
CLI 入口 - 命令行接口
支持运行 Skill 任务、列出 Skills、管理 Windows 定时任务
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.runner import TaskRunner
from src.scheduler.windows import (
    TASK_FOLDER,
    create_task_xml,
    delete_task,
    list_tasks as get_windows_tasks,
    register_task_from_xml,
)


def setup_logging(verbose: bool = False) -> None:
    """配置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def run_single(task_name: str, config_path: str) -> None:
    """运行单个任务"""
    runner = TaskRunner(config_path=config_path)
    runner.load_config()

    result = await runner.run_task(task_name)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


async def run_all_tasks(config_path: str) -> None:
    """运行所有已启用的任务"""
    runner = TaskRunner(config_path=config_path)
    runner.load_config()

    results = await runner.run_all()
    for r in results:
        print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2))


def list_configured_tasks(config_path: str) -> None:
    """列出所有已配置的任务"""
    runner = TaskRunner(config_path=config_path)
    runner.load_config()

    tasks = runner.list_tasks()
    if not tasks:
        print("没有配置任何任务")
        return

    for task in tasks:
        enabled = "启用" if task["enabled"] else "禁用"
        print(f"  {task['name']} [{enabled}] skill={task['skill']} - {task['description']}")
        if task["schedule"]:
            print(f"    计划: {task['schedule']}")


def list_available_skills(config_path: str) -> None:
    """列出所有可用的 Claude Code Skills"""
    runner = TaskRunner(config_path=config_path)
    runner.load_config()

    skills = runner.list_skills()
    if not skills:
        print("没有找到任何 Skill 定义")
        print("请在 .claude/skills/ 目录下创建 SKILL.md 文件")
        return

    for skill in skills:
        print(f"  /{skill['name']}")


def setup_windows_task(task_name: str, schedule: str, config_path: str) -> None:
    """设置 Windows 定时任务"""
    python_args = f"run {task_name} --config {config_path}"

    xml_content = create_task_xml(
        task_name=f"auto_research_{task_name}",
        schedule=schedule,
        python_args=python_args,
        description=f"Auto Research 任务: {task_name}",
    )

    xml_dir = Path("config/windows_tasks")
    xml_dir.mkdir(parents=True, exist_ok=True)
    xml_path = xml_dir / f"{task_name}.xml"
    xml_path.write_text(xml_content, encoding="utf-16")
    print(f"XML 配置已保存到: {xml_path}")

    if register_task_from_xml(xml_path, task_name):
        print(f"Windows 定时任务已注册: {TASK_FOLDER}\\{task_name}")
    else:
        print("注册失败，请手动导入 XML 文件到 Windows 任务计划程序")


def remove_windows_task(task_name: str) -> None:
    """删除 Windows 定时任务"""
    if delete_task(task_name):
        print(f"已删除: {TASK_FOLDER}\\{task_name}")
    else:
        print(f"删除失败: {task_name}")


def list_windows_tasks() -> None:
    """列出 Windows 定时任务"""
    tasks = get_windows_tasks()
    if not tasks:
        print(f"没有找到 {TASK_FOLDER} 相关的 Windows 定时任务")
        return

    for task in tasks:
        print(f"  {task['name']} - 状态: {task['status']} - 下次运行: {task['next_run']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="auto-research",
        description="基于 Claude Agent SDK 的定时任务框架 (Skill 架构)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="详细日志输出")
    parser.add_argument(
        "-c",
        "--config",
        default="config/tasks.yaml",
        help="任务配置文件路径 (默认: config/tasks.yaml)",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # run 命令
    run_parser = subparsers.add_parser("run", help="运行指定任务")
    run_parser.add_argument("task_name", nargs="?", help="任务名称（不指定则运行全部）")

    # list 命令
    subparsers.add_parser("list", help="列出所有已配置的任务")

    # skills 命令
    subparsers.add_parser("skills", help="列出所有可用的 Skills")

    # schedule 命令组
    sched_parser = subparsers.add_parser("schedule", help="管理 Windows 定时任务")
    sched_sub = sched_parser.add_subparsers(dest="sched_action", help="调度操作")

    add_parser = sched_sub.add_parser("add", help="添加 Windows 定时任务")
    add_parser.add_argument("task_name", help="任务名称")
    add_parser.add_argument(
        "--at",
        required=True,
        dest="schedule",
        help='计划表达式 (如 "daily 09:00", "interval 60")',
    )

    rm_parser = sched_sub.add_parser("remove", help="删除 Windows 定时任务")
    rm_parser.add_argument("task_name", help="任务名称")

    sched_sub.add_parser("list", help="列出 Windows 定时任务")

    args = parser.parse_args()
    setup_logging(args.verbose)

    if args.command == "run":
        if args.task_name:
            asyncio.run(run_single(args.task_name, args.config))
        else:
            asyncio.run(run_all_tasks(args.config))

    elif args.command == "list":
        list_configured_tasks(args.config)

    elif args.command == "skills":
        list_available_skills(args.config)

    elif args.command == "schedule":
        if args.sched_action == "add":
            setup_windows_task(args.task_name, args.schedule, args.config)
        elif args.sched_action == "remove":
            remove_windows_task(args.task_name)
        elif args.sched_action == "list":
            list_windows_tasks()
        else:
            sched_parser.print_help()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
