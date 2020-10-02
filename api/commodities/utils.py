def format_commodity_code(code, separator="."):
    code = code.rstrip("0")
    if len(code) % 2:
        code = f"{code}0"
    code_split = [code[i:i + 2] for i in range(0, len(code), 2)]
    if len(code_split) > 2:
        code_split = [code_split[0] + code_split[1]] + code_split[2:]
    return separator.join(code_split)
