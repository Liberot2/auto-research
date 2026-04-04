"""
Windows 任务计划程序集成
通过 schtasks 命令创建和管理 Windows 定时任务
"""

import logging
import subprocess
import sys
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

TASK_FOLDER = "AutoResearch"


def _get_python_path() -> str:
    """获取当前 Python 解释器路径"""
    return sys.executable


def _get_script_path() -> str:
    """获取 CLI 入口脚本路径"""
    return str(Path(__file__).parent / "cli.py")


def _escape_xml(text: str) -> str:
    """转义 XML 特殊字符"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def create_task_xml(
    task_name: str,
    schedule: str,
    python_args: str = "",
    description: str = "",
    working_dir: str | None = None,
) -> str:
    """生成 Windows Task Scheduler XML 配置文件

    支持的计划格式:
        - "daily HH:MM"       每天在指定时间运行
        - "weekly DOW HH:MM"  每周指定星期几运行 (MON,TUE,...)
        - "monthly DD HH:MM"  每月指定日期运行
        - "interval MM"       每 MM 分钟运行一次
        - "onstartup"         系统启动时运行
    """
    python_path = _get_python_path()
    script_path = _get_script_path()
    if working_dir is None:
        working_dir = str(Path.cwd())

    parts = schedule.strip().split()
    if not parts:
        raise ValueError(f"无效的计划格式: {schedule}")

    schedule_type = parts[0].lower()
    today = date.today().isoformat()

    # 构建触发器
    trigger = ET.Element("Triggers")

    if schedule_type == "daily" and len(parts) >= 2:
        time_str = parts[1]
        cal_trigger = ET.SubElement(trigger, "CalendarTrigger")
        ET.SubElement(cal_trigger, "StartBoundary").text = f"{today}T{time_str}:00"
        ET.SubElement(cal_trigger, "Enabled").text = "true"
        schedule_by_day = ET.SubElement(cal_trigger, "ScheduleByDay")
        ET.SubElement(schedule_by_day, "DaysInterval").text = "1"

    elif schedule_type == "weekly" and len(parts) >= 3:
        time_str = parts[2]
        day_of_week = parts[1].upper()
        cal_trigger = ET.SubElement(trigger, "CalendarTrigger")
        ET.SubElement(cal_trigger, "StartBoundary").text = f"{today}T{time_str}:00"
        ET.SubElement(cal_trigger, "Enabled").text = "true"
        schedule_by_week = ET.SubElement(cal_trigger, "ScheduleByWeek")
        ET.SubElement(schedule_by_week, "WeeksInterval").text = "1"
        days_of_week = ET.SubElement(schedule_by_week, "DaysOfWeek")
        ET.SubElement(days_of_week, day_of_week)

    elif schedule_type == "monthly" and len(parts) >= 3:
        time_str = parts[2]
        day = parts[1]
        cal_trigger = ET.SubElement(trigger, "CalendarTrigger")
        ET.SubElement(cal_trigger, "StartBoundary").text = f"{today}T{time_str}:00"
        ET.SubElement(cal_trigger, "Enabled").text = "true"
        schedule_by_month = ET.SubElement(cal_trigger, "ScheduleByMonth")
        days_of_month = ET.SubElement(schedule_by_month, "DaysOfMonth")
        ET.SubElement(days_of_month, "Day").text = day
        months = ET.SubElement(schedule_by_month, "Months")
        for m in range(1, 13):
            ET.SubElement(months, f"Month{m:02d}")

    elif schedule_type == "interval" and len(parts) >= 2:
        minutes = parts[1]
        time_trigger = ET.SubElement(trigger, "TimeTrigger")
        repetition = ET.SubElement(time_trigger, "Repetition")
        ET.SubElement(repetition, "Interval").text = f"PT{minutes}M"
        ET.SubElement(repetition, "StopAtDurationEnd").text = "false"
        ET.SubElement(time_trigger, "StartBoundary").text = f"{today}T00:00:00"
        ET.SubElement(time_trigger, "Enabled").text = "true"

    elif schedule_type == "onstartup":
        boot_trigger = ET.SubElement(trigger, "BootTrigger")
        ET.SubElement(boot_trigger, "Enabled").text = "true"

    else:
        raise ValueError(f"不支持的计划格式: {schedule}")

    # 构建完整任务 XML
    task = ET.Element("Task", version="1.2", xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task")

    reg_info = ET.SubElement(task, "RegistrationInfo")
    ET.SubElement(reg_info, "Description").text = description or task_name
    ET.SubElement(reg_info, "Author").text = "Auto Research"

    task.append(trigger)

    principals = ET.SubElement(task, "Principals")
    principal = ET.SubElement(principals, "Principal", id="Author")
    ET.SubElement(principal, "LogonType").text = "InteractiveToken"
    ET.SubElement(principal, "RunLevel").text = "LeastPrivilege"

    settings = ET.SubElement(task, "Settings")
    ET.SubElement(settings, "MultipleInstancesPolicy").text = "IgnoreNew"
    ET.SubElement(settings, "DisallowStartIfOnBatteries").text = "false"
    ET.SubElement(settings, "StopIfGoingOnBatteries").text = "false"
    ET.SubElement(settings, "AllowHardTerminate").text = "true"
    ET.SubElement(settings, "StartWhenAvailable").text = "true"
    ET.SubElement(settings, "RunOnlyIfNetworkAvailable").text = "false"
    ET.SubElement(settings, "AllowStartOnDemand").text = "true"
    ET.SubElement(settings, "Enabled").text = "true"
    ET.SubElement(settings, "Hidden").text = "false"

    actions = ET.SubElement(task, "Actions", Context="Author")
    exec_elem = ET.SubElement(actions, "Exec")
    ET.SubElement(exec_elem, "Command").text = python_path
    arguments = f'"{script_path}" {python_args}'.strip()
    ET.SubElement(exec_elem, "Arguments").text = arguments
    ET.SubElement(exec_elem, "WorkingDirectory").text = working_dir

    # 转换为字符串，添加 XML 声明
    xml_str = ET.tostring(task, encoding="unicode")
    return f'<?xml version="1.0" encoding="UTF-16"?>\n{xml_str}'


def delete_task(task_name: str) -> bool:
    """删除 Windows 定时任务"""
    cmd = ["schtasks", "/delete", "/tn", f"{TASK_FOLDER}\\{task_name}", "/f"]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Windows 任务已删除: %s", task_name)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("删除 Windows 任务失败: %s\n%s", e, e.stderr)
        return False


def list_tasks() -> list[dict[str, str]]:
    """列出所有 AutoResearch 相关的 Windows 定时任务"""
    cmd = ["schtasks", "/query", "/fo", "csv", "/v"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        tasks = []
        for line in result.stdout.strip().split("\n")[1:]:
            parts = line.strip().strip('"').split('","')
            if len(parts) >= 2 and TASK_FOLDER in parts[0]:
                tasks.append({
                    "name": parts[0],
                    "status": parts[1] if len(parts) > 1 else "unknown",
                    "next_run": parts[2] if len(parts) > 2 else "",
                })
        return tasks
    except subprocess.CalledProcessError as e:
        logger.error("查询 Windows 任务失败: %s", e)
        return []


def register_task_from_xml(xml_path: str | Path, task_name: str) -> bool:
    """通过 XML 文件注册 Windows 定时任务"""
    cmd = ["schtasks", "/create", "/tn", f"{TASK_FOLDER}\\{task_name}", "/xml", str(xml_path), "/f"]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("通过 XML 注册任务成功: %s", task_name)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("通过 XML 注册任务失败: %s\n%s", e, e.stderr)
        return False
