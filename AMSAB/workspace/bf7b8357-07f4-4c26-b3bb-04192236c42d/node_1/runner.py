        # AMSAB Worker — auto-generated runner
        # Task: define search query
        # Tool: python_interpreter
        import json, sys, os

        ARGS = {}

        def run(args):
import io, contextlib
code = args.get("code", args.get("script", ""))
input_data = args.get("input", "")
buf = io.StringIO()
local_vars = {"INPUT": input_data}
with contextlib.redirect_stdout(buf):
    exec(compile(code, "<amsab>", "exec"), local_vars)
return buf.getvalue() or str(local_vars.get("OUTPUT", ""))


        if __name__ == "__main__":
            try:
                result = run(ARGS)
                print(json.dumps({"status": "ok", "output": result}))
            except Exception as exc:
                print(json.dumps({"status": "error", "error": str(exc)}))
                sys.exit(1)
