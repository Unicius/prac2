import copy
import json
from typing import Any


def load_json_file(filename: str) -> dict[str, Any]:
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_text(value: Any) -> bool:
    return isinstance(value, str) and len(value.strip()) >= 1


def check_number(name: str, value: Any, rules: dict[str, Any], errors: list[str]) -> None:
    if not is_number(value):
        errors.append(f"Поле '{name}' должно быть числом (number)")
    elif not (rules["minimum"] <= value <= rules["maximum"]):
        errors.append(f"Поле '{name}'={value} вне границ схемы [{rules['minimum']}; {rules['maximum']}]")


def validate_by_schema(data: dict[str, Any], schema: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    props: dict[str, Any] = schema.get("properties", {})

    for field in schema.get("required", []):
        if field not in data:
            errors.append(f"Отсутствует обязательное поле '{field}'")
    if errors:
        return False, errors

    for name in ("well_id", "field_name"):
        if not is_text(data[name]):
            errors.append(f"Поле '{name}' должно быть непустой строкой")

    depth = data["depth_m"]
    depth_rules = props["depth_m"]
    if not isinstance(depth, int) or isinstance(depth, bool):
        errors.append("Поле 'depth_m' должно быть целым числом (integer)")
    elif not (depth_rules["minimum"] <= depth <= depth_rules["maximum"]):
        errors.append(
            f"Глубина depth_m={depth} вне границ схемы [{depth_rules['minimum']}; {depth_rules['maximum']}]"
        )

    for name in ("q_liq", "w_pct"):
        check_number(name, data[name], props[name], errors)

    if not isinstance(data["is_active"], bool):
        errors.append("Поле 'is_active' должно быть логическим типом (boolean)")

    pump = data["pump"]
    pump_schema = props["pump"]
    if not isinstance(pump, dict):
        errors.append("Поле 'pump' должно быть вложенным словарём (object)")
    else:
        for name in pump_schema["required"]:
            if name not in pump:
                errors.append(f"Во вложенном блоке 'pump' отсутствует поле '{name}'")
        if "model" in pump and not is_text(pump["model"]):
            errors.append("Поле 'pump.model' должно быть непустой строкой")
        if "power_kw" in pump:
            check_number("pump.power_kw", pump["power_kw"], pump_schema["properties"]["power_kw"], errors)

    return len(errors) == 0, errors


def show(title: str, ok: bool, errors: list[str]) -> None:
    status = "УСПЕШНО (VALID)" if ok else "ОТКЛОНЕНО"
    print(f"\n[{title}] -> {status}")
    for err in errors:
        print(f"  x {err}")


if __name__ == "__main__":
    schema_doc = load_json_file("schema.json")
    valid_data = load_json_file("data.json")

    print("=" * 64)
    print("ЗАПУСК ПРОВЕРКИ КОНТРАКТА ДАННЫХ ПО ФАЙЛУ schema.json (Вариант А)")
    print("=" * 64)

    ok1, errs1 = validate_by_schema(valid_data, schema_doc)
    show("Сценарий 1: Эталонный файл data.json", ok1, errs1)

    bad_limits = copy.deepcopy(valid_data)
    bad_limits["depth_m"] = -100
    bad_limits["w_pct"] = 145.0
    ok2, errs2 = validate_by_schema(bad_limits, schema_doc)
    show("Сценарий 2: Нарушение границ (depth=-100, w=145)", ok2, errs2)

    missing_key = copy.deepcopy(valid_data)
    del missing_key["well_id"]
    ok3, errs3 = validate_by_schema(missing_key, schema_doc)
    show("Сценарий 3: Удалено обязательное поле 'well_id'", ok3, errs3)

    bad_type = copy.deepcopy(valid_data)
    bad_type["pump"]["power_kw"] = "сто пятнадцать"
    ok4, errs4 = validate_by_schema(bad_type, schema_doc)
    show("Сценарий 4: Текст вместо числа в pump.power_kw", ok4, errs4)

    broken = load_json_file("broken_data.json")
    ok5, errs5 = validate_by_schema(broken, schema_doc)
    show("Сценарий 5: Файл broken_data.json", ok5, errs5)
