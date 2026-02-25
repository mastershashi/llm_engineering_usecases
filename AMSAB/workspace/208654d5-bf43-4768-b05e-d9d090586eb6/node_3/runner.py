# AMSAB Worker — auto-generated runner
# Task: extract ingredients and instructions from the recipe page
# Tool: python_interpreter
import json, sys, os

ARGS = {
  "code": "data = $[FAILED] {\"status\": \"error\", \"error\": \"Cannot reach https://exact-biryani-recipe-url.com: [SSL: SSLV3_ALERT_HANDSHAKE_FAILURE] ssl/tls alert handshake failure (_ssl.c:1010)\"}$$ print('Ingredients: ') for ingredient in data['ingredients']: print(ingredient) print('Instructions:') for instruction in data['instructions']: print(instruction)"
}

def run(args):
    import io, contextlib, json as _json
    code = args.get("code", args.get("script", "")).strip()
    input_data = args.get("input", "")
    if not code:
        return "Error: no code provided in args"
    buf = io.StringIO()
    local_vars = {"INPUT": input_data, "json": _json}
    with contextlib.redirect_stdout(buf):
        exec(compile(code, "<amsab>", "exec"), local_vars)
    stdout = buf.getvalue().strip()
    output_var = local_vars.get("OUTPUT", "")
    result = stdout or str(output_var) if output_var else stdout
    return result if result else "(no output — add print() calls to your code)"

if __name__ == "__main__":
    try:
        result = run(ARGS)
        print(json.dumps({"status": "ok", "output": result}))
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)
