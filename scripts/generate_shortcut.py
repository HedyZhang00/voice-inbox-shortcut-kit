#!/usr/bin/env python3
import argparse
import json
import plistlib
import subprocess
import uuid
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "config/feishu_config.json"
DEFAULT_OUT_DIR = PROJECT_ROOT / "dist"
SHORTCUT_VERSION = "public-template-20260717"
API_ROOT = "https://open.feishu.cn/open-apis"
DICTATION_STOP_LISTENING = "On Tap"
REMINDER_PATTERN = (
    "提醒我|提醒|日历|日程|开会|会议|客户|医院|课程|上课|预约|约|记得|别忘了|"
    "闹钟|待办|购物清单|买|交|接|送|准备|半小时后|一小时后|明天|后天|下周|"
    "早上|上午|中午|下午|晚上|点|分钟后"
)
CALENDAR_PATTERN = "日历|日程|开会|会议|客户|医院|课程|上课|预约|约|例会|安排"


def new_uuid() -> str:
    return str(uuid.uuid4()).upper()


def plain_text(value: str) -> dict:
    return {
        "Value": {"string": value},
        "WFSerializationType": "WFTextTokenString",
    }


def token_string(output_uuid: str, output_name: str, prefix: str = "", suffix: str = "") -> dict:
    text = f"{prefix}\ufffc{suffix}"
    offset = len(prefix)
    return {
        "Value": {
            "string": text,
            "attachmentsByRange": {
                f"{{{offset}, 1}}": {
                    "Type": "ActionOutput",
                    "OutputUUID": output_uuid,
                    "OutputName": output_name,
                }
            },
        },
        "WFSerializationType": "WFTextTokenString",
    }


def multi_token_string(parts: list[str | tuple[str, str]]) -> dict:
    text_parts: list[str] = []
    attachments: dict[str, dict] = {}
    offset = 0
    for part in parts:
        if isinstance(part, str):
            text_parts.append(part)
            offset += len(part)
            continue
        output_uuid, output_name = part
        text_parts.append("\ufffc")
        attachments[f"{{{offset}, 1}}"] = {
            "Type": "ActionOutput",
            "OutputUUID": output_uuid,
            "OutputName": output_name,
        }
        offset += 1
    return {
        "Value": {
            "string": "".join(text_parts),
            "attachmentsByRange": attachments,
        },
        "WFSerializationType": "WFTextTokenString",
    }


def token_attachment(output_uuid: str, output_name: str) -> dict:
    return {
        "Value": {
            "Type": "ActionOutput",
            "OutputUUID": output_uuid,
            "OutputName": output_name,
        },
        "WFSerializationType": "WFTextTokenAttachment",
    }


def variable_output(output_uuid: str, output_name: str) -> dict:
    return {
        "Type": "Variable",
        "Variable": token_attachment(output_uuid, output_name),
    }


def joined_token_string(outputs: list[tuple[str, str]], separator: str = "\n") -> dict:
    parts: list[str | tuple[str, str]] = []
    for index, output in enumerate(outputs):
        if index:
            parts.append(separator)
        parts.append(output)
    return multi_token_string(parts)


def dictionary_item(key: str, value, item_type: int = 0) -> dict:
    return {
        "UUID": new_uuid(),
        "WFKey": plain_text(key),
        "WFItemType": item_type,
        "WFValue": value if isinstance(value, dict) else plain_text(str(value)),
    }


def shortcuts_dictionary(items: list[dict]) -> dict:
    return {
        "Value": {"WFDictionaryFieldValueItems": items},
        "WFSerializationType": "WFDictionaryFieldValue",
    }


def detect_text(input_uuid: str, input_name: str, output_uuid: str, output_name: str) -> dict:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.detect.text",
        "WFWorkflowActionParameters": {
            "UUID": output_uuid,
            "CustomOutputName": output_name,
            "WFInput": token_attachment(input_uuid, input_name),
        },
    }


def match_text(
    input_uuid: str,
    input_name: str,
    output_uuid: str,
    output_name: str,
    pattern: str = REMINDER_PATTERN,
) -> dict:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.text.match",
        "WFWorkflowActionParameters": {
            "UUID": output_uuid,
            "CustomOutputName": output_name,
            "WFInput": token_attachment(input_uuid, input_name),
            "WFMatchTextPattern": pattern,
            "WFMatchTextCaseSensitive": False,
        },
    }


def detect_date(input_uuid: str, input_name: str, output_uuid: str, output_name: str) -> dict:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.detect.date",
        "WFWorkflowActionParameters": {
            "UUID": output_uuid,
            "CustomOutputName": output_name,
            "WFInput": token_attachment(input_uuid, input_name),
        },
    }


def get_first_item(input_uuid: str, input_name: str, output_uuid: str, output_name: str) -> dict:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist",
        "WFWorkflowActionParameters": {
            "UUID": output_uuid,
            "CustomOutputName": output_name,
            "WFInput": token_attachment(input_uuid, input_name),
            "WFItemSpecifier": "First Item",
        },
    }


def adjust_date(input_uuid: str, input_name: str, output_uuid: str, output_name: str) -> dict:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.adjustdate",
        "WFWorkflowActionParameters": {
            "UUID": output_uuid,
            "CustomOutputName": output_name,
            "WFDate": token_attachment(input_uuid, input_name),
            "WFAdjustOperation": "Add",
            "WFDuration": plain_text("30 minutes"),
        },
    }


def if_no_value(input_uuid: str, input_name: str, group_uuid: str) -> dict:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": group_uuid,
            "WFInput": variable_output(input_uuid, input_name),
            "WFControlFlowMode": 0,
            "WFCondition": 101,
        },
    }


def otherwise(group_uuid: str) -> dict:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": group_uuid,
            "WFControlFlowMode": 1,
        },
    }


def end_if(group_uuid: str) -> dict:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": group_uuid,
            "WFControlFlowMode": 2,
        },
    }


def download_json(url: str, headers: dict, body_items: list[dict], output_uuid: str, output_name: str) -> dict:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
        "WFWorkflowActionParameters": {
            "UUID": output_uuid,
            "CustomOutputName": output_name,
            "ShowHeaders": False,
            "WFURL": url,
            "WFHTTPMethod": "POST",
            "WFHTTPHeaders": shortcuts_dictionary(
                [dictionary_item(key, value) for key, value in headers.items()]
            ),
            "WFHTTPBodyType": "JSON",
            "WFJSONValues": shortcuts_dictionary(body_items),
            "WFAllowsCellularAccess": True,
            "WFAllowsRedirects": True,
            "WFIgnoreCookies": False,
            "WFTimeout": 60,
        },
    }


def detect_dictionary(input_uuid: str, input_name: str, output_uuid: str, output_name: str) -> dict:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.detect.dictionary",
        "WFWorkflowActionParameters": {
            "UUID": output_uuid,
            "CustomOutputName": output_name,
            "WFInput": token_attachment(input_uuid, input_name),
        },
    }


def get_value(input_uuid: str, input_name: str, key: str, output_uuid: str, output_name: str) -> dict:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
        "WFWorkflowActionParameters": {
            "UUID": output_uuid,
            "CustomOutputName": output_name,
            "WFInput": token_attachment(input_uuid, input_name),
            "WFDictionaryKey": key,
        },
    }


def keychain_secret(service: str, account: str) -> str:
    result = subprocess.run(
        ["security", "find-generic-password", "-w", "-s", service, "-a", account],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def add_reminder(note_uuid: str, note_name: str, list_name: str) -> dict:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.addnewreminder",
        "WFWorkflowActionParameters": {
            "UUID": new_uuid(),
            "WFCalendarItemTitle": token_string(note_uuid, note_name),
            "WFCalendarItemCalendar": list_name,
            "WFAlertEnabled": "No Alert",
            "WFCalendarItemNotes": token_string(note_uuid, note_name),
            "WFPriority": "None",
        },
    }


def add_calendar_event(
    note_uuid: str,
    note_name: str,
    start_uuid: str,
    start_name: str,
    end_uuid: str,
    end_name: str,
    calendar_name: str,
) -> dict:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.addnewevent",
        "WFWorkflowActionParameters": {
            "UUID": new_uuid(),
            "WFCalendarItemTitle": token_string(note_uuid, note_name),
            "WFCalendarItemCalendar": calendar_name,
            "WFCalendarItemDates": True,
            "WFCalendarItemStartDate": token_string(start_uuid, start_name),
            "WFCalendarItemEndDate": token_string(end_uuid, end_name),
            "WFCalendarItemAllDay": False,
            "WFAlertTime": "Custom",
            "WFAlertCustomTime": token_string(start_uuid, start_name),
            "WFCalendarItemNotes": token_string(note_uuid, note_name),
        },
    }


def native_reminder_calendar_actions(
    note_uuid: str,
    note_name: str,
    prefix: str,
    reminder_list: str,
    calendar_name: str,
) -> list[dict]:
    calendar_match_uuid = new_uuid()
    calendar_group_uuid = new_uuid()
    dates_uuid = new_uuid()
    date_group_uuid = new_uuid()
    first_date_uuid = new_uuid()
    end_date_uuid = new_uuid()
    return [
        add_reminder(note_uuid, note_name, reminder_list),
        match_text(note_uuid, note_name, calendar_match_uuid, f"{prefix}日历关键词", CALENDAR_PATTERN),
        if_no_value(calendar_match_uuid, f"{prefix}日历关键词", calendar_group_uuid),
        otherwise(calendar_group_uuid),
        detect_date(note_uuid, note_name, dates_uuid, f"{prefix}识别时间"),
        if_no_value(dates_uuid, f"{prefix}识别时间", date_group_uuid),
        otherwise(date_group_uuid),
        get_first_item(dates_uuid, f"{prefix}识别时间", first_date_uuid, f"{prefix}开始时间"),
        adjust_date(first_date_uuid, f"{prefix}开始时间", end_date_uuid, f"{prefix}结束时间"),
        add_calendar_event(
            note_uuid,
            note_name,
            first_date_uuid,
            f"{prefix}开始时间",
            end_date_uuid,
            f"{prefix}结束时间",
            calendar_name,
        ),
        end_if(date_group_uuid),
        end_if(calendar_group_uuid),
    ]


def token_request_actions(config: dict, app_secret: str, response_uuid: str, dict_uuid: str, token_uuid: str) -> list[dict]:
    return [
        download_json(
            f"{API_ROOT}/auth/v3/tenant_access_token/internal",
            {"Content-Type": "application/json; charset=utf-8"},
            [
                dictionary_item("app_id", config["app_id"]),
                dictionary_item("app_secret", app_secret),
            ],
            response_uuid,
            "token接口返回",
        ),
        detect_dictionary(response_uuid, "token接口返回", dict_uuid, "token字典"),
        get_value(dict_uuid, "token字典", "tenant_access_token", token_uuid, "tenant_access_token"),
    ]


def create_record_actions(
    config: dict,
    token_uuid: str,
    note_value: dict,
    idea_id_value: dict,
    response_uuid: str,
    dict_uuid: str,
    code_uuid: str,
    msg_uuid: str,
    *,
    input_type: str = "灵感想法",
    action_status: str = "待判断",
    include_idea_fields: bool = True,
) -> list[dict]:
    names = {
        "text": "文本",
        "idea_id": "灵感ID",
        "note": "灵感备注",
        "source_platform": "来源平台",
        "capture_method": "采集方式",
        "input_type": "输入类型",
        "action_status": "行动状态",
        "sync_status": "本地同步状态",
        "next_use": "下一步用途",
        "implementation_path": "实现路径",
        "importance": "重要度",
        "status": "状态",
    }
    names.update(config.get("field_names", {}))
    field_items = [
        dictionary_item(names["text"], note_value),
        dictionary_item(names["idea_id"], idea_id_value),
        dictionary_item(names["note"], note_value),
        dictionary_item(names["source_platform"], "其他"),
        dictionary_item(names["capture_method"], "语音"),
        dictionary_item(names["input_type"], input_type),
        dictionary_item(names["action_status"], action_status),
        dictionary_item(names["sync_status"], "已同步"),
    ]
    if include_idea_fields:
        field_items.extend(
            [
                dictionary_item(names["next_use"], "待判断"),
                dictionary_item(names["implementation_path"], "待判断"),
                dictionary_item(names["importance"], "3", item_type=3),
                dictionary_item(names["status"], "raw"),
            ]
        )
    fields = shortcuts_dictionary(field_items)
    return [
        download_json(
            (
                f"{API_ROOT}/bitable/v1/apps/{config['app_token']}"
                f"/tables/{config['table_id']}/records"
            ),
            {
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": token_string(token_uuid, "tenant_access_token", prefix="Bearer "),
            },
            [dictionary_item("fields", fields, item_type=1)],
            response_uuid,
            "新增记录返回",
        ),
        detect_dictionary(response_uuid, "新增记录返回", dict_uuid, "新增记录字典"),
        get_value(dict_uuid, "新增记录字典", "code", code_uuid, "create_code"),
        get_value(dict_uuid, "新增记录字典", "msg", msg_uuid, "create_msg"),
    ]


def build_shortcut(config: dict, app_secret: str, shortcut_name: str) -> dict:
    current_date_uuid = new_uuid()
    voice_note_uuid = new_uuid()
    edited_note_uuid = new_uuid()
    create_match_uuid = new_uuid()
    create_type_group_uuid = new_uuid()
    token_response_uuid = new_uuid()
    token_dict_uuid = new_uuid()
    token_uuid = new_uuid()
    create_response_uuid = new_uuid()
    create_dict_uuid = new_uuid()
    create_code_uuid = new_uuid()
    create_msg_uuid = new_uuid()
    reminder_token_response_uuid = new_uuid()
    reminder_token_dict_uuid = new_uuid()
    reminder_token_uuid = new_uuid()
    reminder_response_uuid = new_uuid()
    reminder_dict_uuid = new_uuid()
    reminder_code_uuid = new_uuid()
    reminder_msg_uuid = new_uuid()

    idea_id = multi_token_string(["iphone_openapi_voice_", (current_date_uuid, "当前日期")])
    current_note = token_string(edited_note_uuid, "最终文本")

    shortcut = {
        "WFWorkflowClientRelease": "26.0",
        "WFWorkflowClientVersion": "3107",
        "WFWorkflowIcon": {
            "WFWorkflowIconGlyphNumber": 61440,
            "WFWorkflowIconStartColor": 4282601983,
        },
        "WFWorkflowImportQuestions": [],
        "WFWorkflowInputContentItemClasses": [
            "WFURLContentItem",
            "WFTextContentItem",
            "WFWebPageContentItem",
            "WFStringContentItem",
        ],
        "WFWorkflowMinimumClientVersion": 1300,
        "WFWorkflowMinimumClientVersionString": "1300",
        "WFWorkflowOutputContentItemClasses": [],
        "WFWorkflowHasOutputFallback": False,
        "WFWorkflowTypes": ["ActionExtension", "MenuBar", "Watch"],
        "WFWorkflowHasShortcutInputVariables": True,
        "WFWorkflowName": shortcut_name,
        "WFWorkflowActions": [
            {
                "WFWorkflowActionIdentifier": "is.workflow.actions.comment",
                "WFWorkflowActionParameters": {
                    "WFCommentActionText": (
                        f"OpenAPI语音版 {SHORTCUT_VERSION}：唯一测试入口。默认中文语音听写，停止方式固定为 On Tap；"
                        "语音结束后只弹一次可编辑文本框，默认填入语音识别结果，供用户键盘修改；"
                        "不保存、覆盖、清空或删除本地待同步文件；"
                        "避免 iOS 弹出删除/覆盖文件确认框。"
                    )
                },
            },
            {
                "WFWorkflowActionIdentifier": "is.workflow.actions.date",
                "WFWorkflowActionParameters": {
                    "UUID": current_date_uuid,
                    "CustomOutputName": "当前日期",
                },
            },
            {
                "WFWorkflowActionIdentifier": "is.workflow.actions.dictatetext",
                "WFWorkflowActionParameters": {
                    "UUID": voice_note_uuid,
                    "CustomOutputName": "语音备注",
                    "WFSpeechLanguage": "zh-CN",
                    "WFDictateTextStopListening": DICTATION_STOP_LISTENING,
                },
            },
            {
                "WFWorkflowActionIdentifier": "is.workflow.actions.ask",
                "WFWorkflowActionParameters": {
                    "UUID": edited_note_uuid,
                    "CustomOutputName": "最终文本",
                    "WFAllowsMultilineText": True,
                    "WFAskActionPrompt": "检查并修改识别文字",
                    "WFInputType": "Text",
                    "WFAskActionDefaultAnswer": token_string(voice_note_uuid, "语音备注"),
                },
            },
            match_text(edited_note_uuid, "最终文本", create_match_uuid, "提醒关键词"),
            if_no_value(create_match_uuid, "提醒关键词", create_type_group_uuid),
            *token_request_actions(config, app_secret, token_response_uuid, token_dict_uuid, token_uuid),
            *create_record_actions(
                config,
                token_uuid,
                current_note,
                idea_id,
                create_response_uuid,
                create_dict_uuid,
                create_code_uuid,
                create_msg_uuid,
            ),
            otherwise(create_type_group_uuid),
            *native_reminder_calendar_actions(
                edited_note_uuid,
                "最终文本",
                "",
                config.get("reminder_list", "提醒事项"),
                config.get("calendar_name", "个人"),
            ),
            *token_request_actions(
                config,
                app_secret,
                reminder_token_response_uuid,
                reminder_token_dict_uuid,
                reminder_token_uuid,
            ),
            *create_record_actions(
                config,
                reminder_token_uuid,
                current_note,
                idea_id,
                reminder_response_uuid,
                reminder_dict_uuid,
                reminder_code_uuid,
                reminder_msg_uuid,
                input_type="提醒事项",
                action_status="待处理",
                include_idea_fields=False,
            ),
            end_if(create_type_group_uuid),
        ],
    }

    return shortcut


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the Linggan voice inbox Apple Shortcut."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--name", default="灵感快收")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Build with a redacted secret, print action counts, and write no files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    app_secret = "REDACTED_FOR_VALIDATION"
    if not args.validate_only:
        app_secret = keychain_secret(
            config.get("app_secret_keychain_service") or "linggan-voice-inbox.feishu",
            config["app_secret_keychain_account"],
        )

    shortcut = build_shortcut(config, app_secret, args.name)
    actions = shortcut["WFWorkflowActions"]
    counts = {
        "dictation": sum(
            action["WFWorkflowActionIdentifier"] == "is.workflow.actions.dictatetext"
            for action in actions
        ),
        "editable_text_box": sum(
            action["WFWorkflowActionIdentifier"] == "is.workflow.actions.ask"
            for action in actions
        ),
        "notification": sum(
            action["WFWorkflowActionIdentifier"] == "is.workflow.actions.notification"
            for action in actions
        ),
        "file_actions": sum(
            action["WFWorkflowActionIdentifier"]
            in {
                "is.workflow.actions.documentpicker.save",
                "is.workflow.actions.documentpicker.open",
                "is.workflow.actions.file.delete",
            }
            for action in actions
        ),
    }
    if args.validate_only:
        print(json.dumps(counts, ensure_ascii=False, indent=2))
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)
    unsigned = args.output_dir / f"{args.name}.unsigned.shortcut"
    signed = args.output_dir / f"{args.name}.shortcut"
    tmp_unsigned = Path("/tmp/linggan-public.unsigned.shortcut")
    tmp_signed = Path("/tmp/linggan-public.shortcut")

    with unsigned.open("wb") as handle:
        plistlib.dump(shortcut, handle, fmt=plistlib.FMT_BINARY)

    tmp_unsigned.write_bytes(unsigned.read_bytes())
    tmp_signed.unlink(missing_ok=True)
    subprocess.run(
        [
            "shortcuts",
            "sign",
            "--mode",
            "anyone",
            "--input",
            str(tmp_unsigned),
            "--output",
            str(tmp_signed),
        ],
        check=True,
    )
    signed.write_bytes(tmp_signed.read_bytes())
    unsigned.unlink(missing_ok=True)
    tmp_unsigned.unlink(missing_ok=True)
    tmp_signed.unlink(missing_ok=True)
    print(signed)


if __name__ == "__main__":
    main()
