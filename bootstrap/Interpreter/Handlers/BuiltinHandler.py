import os
import sys
import time
import subprocess
import math
import json
import re
import random as py_random
import struct
import socket
import hashlib
import base64
import urllib.request
import urllib.error
from typing import Any, Optional

from Interpreter.Runtime import (
    InputStream,
    OutputStream,
    BuiltinCapability,
    StringCapability,
    MemoryCapability,
    FileCapability,
    FileInstance,
    SysCapability,
    TimeCapability,
    ProcessInstance,
    ProcessCapability,
    MapCapability,
    TermCapability,
    FunctionObject,
    SetCapability,
    RandomCapability,
    NetCapability,
    SocketInstance,
    CryptoCapability,
)

class BuiltinHandler:
    def _register_builtins(self) -> None:
        self.global_environment.define("nothing", None, mutable=False, type="Void")
        
        def _input_read(prompt=""):
            try:
                return input(prompt)
            except EOFError:
                return ""

        def _input_read_line():
            try:
                line = sys.stdin.readline()
                if not line:
                    return None
                return line.rstrip("\r\n")
            except Exception:
                return None

        def _input_read_exact(count):
            try:
                n = int(count)
                if n <= 0:
                    return ""
                return sys.stdin.read(n)
            except Exception:
                return ""

        in_obj = InputStream("in", {
            "read": _input_read,
            "read_line": _input_read_line,
            "read_exact": _input_read_exact
        })

        self.global_environment.define(
            "__builtin_input", in_obj, mutable=False, type="InputStream"
        )

        # Register 'out' capability
        def _out_write(value, data=None):
            if data and isinstance(data, dict):
                # Simple interpolation for structured output
                for k, v in data.items():
                    value = str(value).replace(f"{{{k}}}", str(v))
            print(value, end="", flush=True)
            return None

        def _out_write_raw(value):
            if value is not None:
                sys.stdout.write(str(value))
                sys.stdout.flush()
            return None

        def _out_info(value):
            print(f"\033[34m[INFO]\033[0m {value}")
            return None

        def _out_warn(value):
            print(f"\033[33m[WARN]\033[0m {value}")
            return None

        def _out_error(value):
            print(f"\033[31m[ERROR]\033[0m {value}", file=sys.stderr)
            return None

        def _out_debug(value):
            if self.debugging:
                print(f"\033[36m[DEBUG]\033[0m {value}")
            return None

        out_obj = OutputStream("out", {
            "write": _out_write,
            "write_raw": _out_write_raw,
            "writeln": lambda v: _out_write(str(v) + "\n"),
            "write_line": lambda v: _out_write(str(v) + "\n"),
            "info": _out_info,
            "warn": _out_warn,
            "error": _out_error,
            "debug": _out_debug,
            "flush": lambda: (sys.stdout.flush(), None)[1]
        })

        self.global_environment.define(
            "__builtin_output", out_obj, mutable=False, type="OutputStream"
        )
        err_obj = OutputStream("stderr", {
            "write": lambda v: (sys.stderr.write(str(v)), sys.stderr.flush(), None)[2],
            "writeln": lambda v="": (sys.stderr.write(str(v) + "\n"), sys.stderr.flush(), None)[2],
            "write_line": lambda v="": (sys.stderr.write(str(v) + "\n"), sys.stderr.flush(), None)[2],
            "flush": lambda: (sys.stderr.flush(), None)[1]
        })
        self.global_environment.define("stdout", out_obj, mutable=False, type="OutputStream")
        self.global_environment.define("stderr", err_obj, mutable=False, type="OutputStream")
        self.global_environment.define("stdin", in_obj, mutable=False, type="InputStream")
        self.global_environment.define("write", _out_write, mutable=False, type="Function")
        self.global_environment.define("write_line", lambda v="": _out_write(str(v) + "\n"), mutable=False, type="Function")
        self.global_environment.define("writeln", lambda v="": _out_write(str(v) + "\n"), mutable=False, type="Function")
        self.global_environment.define("read", _input_read, mutable=False, type="Function")
        self.global_environment.define("read_line", _input_read_line, mutable=False, type="Function")
        self.global_environment.define("readln", _input_read_line, mutable=False, type="Function")
        self.global_environment.define("args", sys.argv[1:], mutable=False, type="List")
        self.global_environment.define("env", dict(os.environ), mutable=False, type="Map")

        def _zen_type(v=None):
            if v is None: return "Nothing"
            if isinstance(v, bool): return "Boolean"
            if isinstance(v, int): return "Integer"
            if isinstance(v, float): return "Decimal"
            if isinstance(v, str): return "String"
            if isinstance(v, list): return "List"
            if isinstance(v, set): return "Set"
            if isinstance(v, dict):
                if "kind" in v and v["kind"] is not None: return str(v["kind"])
                if "__type__" in v and v["__type__"] is not None: return str(v["__type__"])
                return "Map"
            from Interpreter.Runtime import BaseObject
            if isinstance(v, BaseObject) and v.name: return v.name
            if hasattr(v, "type_name"): return getattr(v, "type_name")
            if hasattr(v, "kind"): return str(getattr(v, "kind"))
            if type(v).__name__ == "_DefaultSentinel" or str(v) == "Default": return "Default"
            if callable(v): return "Function"
            return "Variant"

        self.global_environment.define("type", _zen_type, mutable=False, type="Function")
 
        # Register '__builtin' object
        def _builtin_error(msg):
            from Interpreter.Interpreter import RaiseException
            err_obj = msg if isinstance(msg, dict) and msg.get("__type__") == "Error" else {"__type__": "Error", "message": msg}
            raise RaiseException(err_obj)
            
        def _create_object(type_name, data):
            # This is a bit complex as we need to find the type in the environments
            # For now, let's look in the global environment
            try:
                type_obj = self.global_environment.get(type_name)
                from Interpreter.Runtime import StructureObject, ClassObject, InstanceObject
                
                if isinstance(type_obj, StructureObject):
                    # It's actually a bit tricky because StructureObject in Runtime.py 
                    # is the instance. We need the template.
                    # In Zenlang, StructureStatement defines the template.
                    # But the interpreter doesn't store the template separately easily.
                    pass
                
                if isinstance(type_obj, ClassObject):
                    # We can create an instance
                    instance_members = {}
                    for m_ast in type_obj.members_ast:
                        m_name = m_ast.name.name
                        m_val = data.get(m_name, None)
                        instance_members[m_name] = {"value": m_val, "mutable": True}
                    return InstanceObject(type_obj, instance_members)
            except:
                pass
            return data

        def _instantiate(class_obj, data):
            from Interpreter.Runtime import ClassObject, InstanceObject
            if not isinstance(class_obj, ClassObject):
                 return data
            
            instance_members = {}
            for m_ast in class_obj.members_ast:
                m_name = m_ast.name
                m_val = data.get(m_name, None)
                instance_members[m_name] = {"value": m_val, "mutable": True}
            
            return InstanceObject(class_obj, instance_members)

        def _pack_binary(spec, data):
            fmt = "<"
            values = []
            for field, type_name in spec.items():
                if type_name == "u8": fmt += "B"; values.append(data[field])
                elif type_name == "i8": fmt += "b"; values.append(data[field])
                elif type_name == "u16": fmt += "H"; values.append(data[field])
                elif type_name == "i16": fmt += "h"; values.append(data[field])
                elif type_name == "u32": fmt += "I"; values.append(data[field])
                elif type_name == "i32": fmt += "i"; values.append(data[field])
            return bytearray(struct.pack(fmt, *values))

        def _unpack_binary(spec, bytes_data):
            fmt = "<"
            fields = []
            for field, type_name in spec.items():
                fields.append(field)
                if type_name == "u8": fmt += "B"
                elif type_name == "i8": fmt += "b"
                elif type_name == "u16": fmt += "H"
                elif type_name == "i16": fmt += "h"
                elif type_name == "u32": fmt += "I"
                elif type_name == "i32": fmt += "i"
            unpacked = struct.unpack(fmt, bytes_data)
            return {fields[i]: unpacked[i] for i in range(len(fields))}

        from Interpreter.Runtime import VariantObject
        
        result_obj = BuiltinCapability("Result", {
            "Ok": lambda val: VariantObject("Result", "Ok", [val]),
            "Error": lambda err: VariantObject("Result", "Error", [err])
        })
        self.global_environment.define("Result", result_obj, mutable=False, type="BuiltinCapability")
        
        option_obj = BuiltinCapability("Option", {
            "Some": lambda val: VariantObject("Option", "Some", [val]),
            "Nothing": lambda: VariantObject("Option", "Nothing", [])
        })
        self.global_environment.define("Option", option_obj, mutable=False, type="BuiltinCapability")

        builtin_obj = BuiltinCapability("__builtin", {
            "error": _builtin_error,
            "error_literal": lambda msg: {"__type__": "Error", "message": msg},
            "range": lambda start, end: list(range(start, end)),
            "create_object": _create_object,
            "instantiate": _instantiate,
            "get_env": lambda name, default=None: os.environ.get(name, default),
            "set_env": lambda name, value: os.environ.__setitem__(name, str(value)),
            "list_env": lambda: list(os.environ.keys()),
            "has_env": lambda name: name in os.environ,
            "create_bytes_size": lambda size: bytearray(size),
            "create_bytes_list": lambda l: bytearray(l),
            "string_to_bytes": lambda s: bytearray(s, "utf-8"),
            "bytes_to_string": lambda b: b.decode("utf-8") if isinstance(b, (bytes, bytearray)) else "".join(chr(int(x) & 0xFF) for x in b),
            "bytes_from_string": lambda s: bytearray(s, "utf-8"),
            "pack_binary": _pack_binary,
            "unpack_binary": _unpack_binary,
        })
        self.global_environment.define("__builtin", builtin_obj, mutable=False, type="BuiltinCapability")
 
        self.global_environment.define("__builtin_output", out_obj, mutable=False, type="OutputStream")
        self.global_environment.define("io", out_obj, mutable=False, type="OutputStream")
        self.global_environment.define("out", out_obj, mutable=False, type="OutputStream")
        
 
        # Register 'string' capability
        string_obj = StringCapability("string", {
            "split": lambda s, sep: s.split(sep),
            "join": lambda parts, sep: sep.join(parts),
            "trim": lambda s: s.strip(),
            "substring": lambda s, start, end=None: s[start:end] if end is not None else s[start:],
            "starts_with": lambda s, prefix: s.startswith(prefix),
            "ends_with": lambda s, suffix: s.endswith(suffix),
            "replace": lambda s, old, new: s.replace(old, new),
            "contains": lambda s, sub: sub in s,
            "length": lambda s: len(s),
            "to_lower": lambda s: s.lower(),
            "to_upper": lambda s: s.upper(),
            "index_of": lambda s, sub: s.find(sub),
            "at": lambda s, i: s[i] if 0 <= i < len(s) else "",
            "byte_at": lambda s, i: ord(s[i]) if 0 <= i < len(s) else -1,
            "to_string": lambda x: str(x),
            "to_number": lambda s: float(s) if '.' in s else int(s),
        })
 
        self.global_environment.define("__builtin_string", string_obj, mutable=False, type="StringCapability")
 
        # Register 'memory' capability
        memory_obj = MemoryCapability("memory", {
            "create_arena": lambda size: self.memory_manager.create_arena(size),
            "free_arena": lambda a: self.memory_manager.free_arena(a),
            "reset_arena": lambda a: a.reset() if hasattr(a, "reset") else None,
            "push_arena": lambda a: self.memory_manager.push_arena(a),
            "pop_arena": lambda: self.memory_manager.pop_arena(),
            "current": lambda: self.memory_manager.get_current_arena(),
            "using_arena": lambda: self.memory_manager.get_current_arena() is not None,
            "arena_depth": lambda: len(self.memory_manager.arena_stack),
            "arena_allocated": lambda *args: 0,
            "arena_capacity": lambda *args: 0,
            "arena_chunks": lambda *args: 0,
            "arena_stats": lambda *args: {"allocated": 0, "capacity": 0, "chunks": 0},
        })
        self.global_environment.define("__builtin_memory", memory_obj, mutable=False, type="MemoryCapability")
        ast_obj = BuiltinCapability("ast", {
            "token": lambda kind, start, length, line, col, el, ec: [kind, start, length, line, col, el, ec],
            "create0": lambda k, l, c: [k, l, c],
            "create1": lambda k, l, c, s0: [k, l, c, s0],
            "create2": lambda k, l, c, s0, s1: [k, l, c, s0, s1],
            "create3": lambda k, l, c, s0, s1, s2: [k, l, c, s0, s1, s2],
            "create4": lambda k, l, c, s0, s1, s2, s3: [k, l, c, s0, s1, s2, s3],
            "create5": lambda k, l, c, s0, s1, s2, s3, s4: [k, l, c, s0, s1, s2, s3, s4],
            "create": lambda k, l, c, s0, s1, s2, s3, s4, s5: [k, l, c, s0, s1, s2, s3, s4, s5],
        })
        self.global_environment.define("__builtin_ast", ast_obj, mutable=False, type="BuiltinCapability")
        self.global_environment.define("ast", ast_obj, mutable=False, type="BuiltinCapability")
        self.global_environment.define("string", string_obj, mutable=False, type="StringCapability")
 
        # Register 'file' capability
        def read_file(path):
            with open(path, 'r') as f:
                return f.read()
 
        def write_file(path, content, mode='w'):
            with open(path, mode) as f:
                f.write(content)
                return True
 
        def write_file_bytes(path, byte_list):
            with open(path, 'wb') as f:
                f.write(bytes(byte_list))
                return True
 
        class FileInstanceObject(FileInstance):
            def __init__(self, path, mode):
                self.handle = open(path, mode)
                super().__init__("File", {
                    "read": lambda: self.handle.read(),
                    "write": lambda v: self.handle.write(v),
                    "close": lambda: self.handle.close(),
                })
 
        def _list_dir(path):
            try:
                return os.listdir(path)
            except OSError:
                return []

        def _mkdir(path):
            try:
                if os.path.isdir(path):
                    return True
                os.mkdir(path)
                return True
            except OSError:
                return False

        def _mkdir_p(path):
            try:
                os.makedirs(path, exist_ok=True)
                return True
            except OSError:
                return False

        def _remove_path(path):
            try:
                if not os.path.exists(path):
                    return False
                if os.path.isdir(path) and not os.path.islink(path):
                    os.rmdir(path)
                else:
                    os.remove(path)
                return True
            except OSError:
                return False

        file_obj = FileCapability("file", {
            "open": lambda path, mode="r": FileInstanceObject(path, mode),
            "read": read_file,
            "write": write_file,
            "write_bytes": write_file_bytes,
            "append": lambda path, content: write_file(path, content, 'a'),
            "exists": lambda path: os.path.exists(path),
            "remove": _remove_path,
            "is_file": lambda path: os.path.isfile(path),
            "is_dir": lambda path: os.path.isdir(path),
            "list_dir": _list_dir,
            "mkdir": _mkdir,
            "mkdir_p": _mkdir_p,
        })
 
        self.global_environment.define("__builtin_file", file_obj, mutable=False, type="FileCapability")
        self.global_environment.define("file", file_obj, mutable=False, type="FileCapability")
 
        # Register 'sys' capability
        def _chdir(path):
            try:
                os.chdir(path)
                return True
            except OSError:
                return False

        sys_obj = SysCapability("sys", {
            "get_args": lambda: self.execution_arguments,
            "exit": lambda code=0: os._exit(code),
            "get_env": lambda key: os.environ.get(key, ""),
            "set_env": lambda key, value: os.environ.__setitem__(key, str(value)),
            "unset_env": lambda key: os.environ.pop(key, None),
            "get_env_map": lambda: dict(os.environ),
            "get_cwd": lambda: os.getcwd(),
            "chdir": _chdir,
            "platform": lambda: sys.platform,
            "version": lambda: "0.1.0-bootstrap",
            "exec": lambda cmd: os.system(cmd),
        })
 
        self.global_environment.define("__builtin_sys", sys_obj, mutable=False, type="SysCapability")
        self.global_environment.define("sys", sys_obj, mutable=False, type="SysCapability")
 
        # Register 'time' capability
        time_obj = TimeCapability("time", {
            "now": lambda: time.time(),
            "monotonic": lambda: time.monotonic(),
            "wallclock": lambda: time.time(),
            "sleep": lambda s: time.sleep(s),
        })
        self.global_environment.define("__builtin_time", time_obj, mutable=False, type="TimeCapability")
        self.global_environment.define("time", time_obj, mutable=False, type="TimeCapability")
 
        # Register 'process' capability
        class ProcessInstanceObject(ProcessInstance):
            def __init__(self, cmd, args):
                self.proc = subprocess.Popen([cmd] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                super().__init__("Process", {
                    "wait": lambda: self.proc.wait(),
                    "get_stdout": lambda: self.proc.stdout.read(),
                    "get_stderr": lambda: self.proc.stderr.read(),
                    "get_code": lambda: self.proc.returncode,
                    "kill": lambda: self.proc.kill(),
                })
 
        def _merge_env(env_overlay):
            merged = os.environ.copy()
            if not env_overlay:
                return merged
            if isinstance(env_overlay, dict):
                for k, v in env_overlay.items():
                    merged[str(k)] = "" if v is None else str(v)
            return merged

        def _shell(cmd, cwd=None, env=None):
            try:
                return subprocess.check_output(
                    cmd if isinstance(cmd, str) else str(cmd),
                    shell=True,
                    text=True,
                    stderr=subprocess.STDOUT,
                    cwd=cwd if cwd else None,
                    env=_merge_env(env),
                )
            except subprocess.CalledProcessError as e:
                return e.output if e.output is not None else ""

        def _shell_result(cmd, cwd=None, env=None):
            p = subprocess.run(
                cmd if isinstance(cmd, str) else str(cmd),
                shell=True,
                text=True,
                capture_output=True,
                cwd=cwd if cwd else None,
                env=_merge_env(env),
            )
            return {
                "stdout": p.stdout or "",
                "stderr": p.stderr or "",
                "code": p.returncode if p.returncode is not None else 1,
            }

        def _shell_in(cwd, cmd):
            return _shell(cmd, cwd=cwd if cwd else None)

        def _shell_result_in(cwd, cmd):
            return _shell_result(cmd, cwd=cwd if cwd else None)

        def _shell_env(env, cmd):
            return _shell(cmd, env=env)

        def _shell_result_env(env, cmd):
            return _shell_result(cmd, env=env)

        def _shell_in_env(cwd, env, cmd):
            return _shell(cmd, cwd=cwd if cwd else None, env=env)

        def _shell_result_in_env(cwd, env, cmd):
            return _shell_result(cmd, cwd=cwd if cwd else None, env=env)

        def _pipeline_run(stages, cwd=None, env=None):
            """Real multi-process pipe: stages is list of argv lists."""
            if not stages:
                return {"stdout": "", "stderr": "", "code": 0}
            stage_lists = []
            for st in stages:
                if isinstance(st, (list, tuple)):
                    stage_lists.append([str(x) for x in st])
                else:
                    stage_lists.append([str(st)])
            env_merged = _merge_env(env)
            procs = []
            prev_stdout = None
            try:
                for i, argv in enumerate(stage_lists):
                    is_last = i == len(stage_lists) - 1
                    p = subprocess.Popen(
                        argv,
                        stdin=prev_stdout if prev_stdout is not None else subprocess.DEVNULL,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE if is_last else subprocess.DEVNULL,
                        cwd=cwd if cwd else None,
                        env=env_merged,
                        text=True,
                    )
                    if prev_stdout is not None:
                        prev_stdout.close()
                    prev_stdout = p.stdout
                    procs.append(p)
                last = procs[-1]
                out, err = last.communicate()
                code = last.returncode if last.returncode is not None else 1
                for p in procs[:-1]:
                    try:
                        p.wait(timeout=5)
                    except Exception:
                        p.kill()
                return {
                    "stdout": out or "",
                    "stderr": err or "",
                    "code": code,
                }
            except Exception as e:
                for p in procs:
                    try:
                        p.kill()
                    except Exception:
                        pass
                return {"stdout": "", "stderr": str(e), "code": 1}

        def _shell_each_line(cmd, fn, cwd=None, env=None):
            count = 0
            try:
                p = subprocess.Popen(
                    cmd if isinstance(cmd, str) else str(cmd),
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=cwd if cwd else None,
                    env=_merge_env(env),
                    text=True,
                )
                assert p.stdout is not None
                for line in p.stdout:
                    line = line.rstrip("\n\r")
                    if isinstance(fn, FunctionObject):
                        self._call_function(fn, [line])
                    elif callable(fn):
                        fn(line)
                    count += 1
                p.wait()
            except Exception:
                pass
            return count

        def _shell_each_line_in(cwd, cmd, fn):
            return _shell_each_line(cmd, fn, cwd=cwd if cwd else None)

        def _shell_each_line_env(env, cmd, fn):
            return _shell_each_line(cmd, fn, env=env)

        def _run_argv(cmd, args=None):
            if args is None:
                args = []
            try:
                return subprocess.check_output([cmd] + list(args), text=True, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                return e.output if e.output is not None else ""

        process_obj = ProcessCapability("process", {
            "spawn": lambda cmd, args=[]: ProcessInstanceObject(cmd, args),
            "run": _run_argv,
            "get_id": lambda: os.getpid(),
            "shell": _shell,
            "shell_result": _shell_result,
            "shell_in": _shell_in,
            "shell_result_in": _shell_result_in,
            "shell_env": _shell_env,
            "shell_result_env": _shell_result_env,
            "shell_in_env": _shell_in_env,
            "shell_result_in_env": _shell_result_in_env,
            "pipeline_run": _pipeline_run,
            "shell_each_line": _shell_each_line,
            "shell_each_line_in": _shell_each_line_in,
            "shell_each_line_env": _shell_each_line_env,
        })
        self.global_environment.define("__builtin_process", process_obj, mutable=False, type="ProcessCapability")
        self.global_environment.define("process", process_obj, mutable=False, type="ProcessCapability")
 
        # Register 'math' capability
        math_obj = BuiltinCapability("math", {
            "abs": lambda x: abs(x),
            "sqrt": lambda x: math.sqrt(x),
            "pow": lambda x, y: math.pow(x, y),
            "sin": lambda x: math.sin(x),
            "cos": lambda x: math.cos(x),
            "tan": lambda x: math.tan(x),
            "asin": lambda x: math.asin(x),
            "acos": lambda x: math.acos(x),
            "atan": lambda x: math.atan(x),
            "atan2": lambda y, x: math.atan2(y, x),
            "exp": lambda x: math.exp(x),
            "log": lambda x: math.log(x),
            "floor": lambda x: math.floor(x),
            "ceil": lambda x: math.ceil(x),
            "round": lambda x: round(x) if isinstance(x, int) else float(round(x)),
            "pi": math.pi,
            "e": math.e,
        })
        self.global_environment.define("__builtin_math", math_obj, mutable=False, type="MathCapability")
 
        # Register 'dictionary' capability
        map_obj = MapCapability("map", {
            "keys": lambda d: list(d.keys()) if isinstance(d, dict) else [],
            "values": lambda d: list(d.values()) if isinstance(d, dict) else [],
            "items": lambda d: (
                [{"key": k, "value": v} for k, v in d.items()]
                if isinstance(d, dict)
                else []
            ),
            "has": lambda d, k: k in d if isinstance(d, dict) else False,
        })
        self.global_environment.define("__builtin_map", map_obj, mutable=False, type="MapCapability")

        # Reflect type registry: name -> {fields, methods, reflectable}
        self._reflect_types: dict = {}

        def _reflect_register_type(type_name, fields, methods, reflectable):
            if not reflectable:
                return
            self._reflect_types[type_name] = {
                "fields": list(fields or []),
                "methods": list(methods or []),
                "reflectable": True,
            }

        self._reflect_register_type = _reflect_register_type

        def _type_name_of(x):
            if isinstance(x, dict):
                if "kind" in x and x["kind"] and x["kind"] != "Map":
                    # Prefer registered structure kind
                    if x["kind"] in self._reflect_types:
                        return x["kind"]
                return "Map"
            if isinstance(x, StructureObject):
                return x.name
            if isinstance(x, InstanceObject):
                return x.class_object.name
            if isinstance(x, ClassObject):
                return x.name
            if isinstance(x, FunctionObject):
                return "Function"
            if isinstance(x, bool):
                return "Boolean"
            if isinstance(x, int):
                return "Integer"
            if isinstance(x, float):
                return "Decimal"
            if isinstance(x, str):
                return "String"
            if isinstance(x, list):
                return "List"
            if isinstance(x, set):
                return "Set"
            if x is None:
                return "Nothing"
            if hasattr(x, "name") and isinstance(x, BaseObject):
                return getattr(x, "name", type(x).__name__)
            return type(x).__name__

        def _meta_for(x):
            tn = _type_name_of(x)
            return self._reflect_types.get(tn)

        def _fields(x):
            meta = _meta_for(x)
            if meta and meta.get("reflectable"):
                return list(meta.get("fields") or [])
            if isinstance(x, StructureObject) and getattr(x, "reflectable", False):
                return x.field_names()
            if isinstance(x, InstanceObject) and getattr(x.class_object, "reflectable", False):
                return x.class_object.field_names()
            if isinstance(x, ClassObject) and getattr(x, "reflectable", False):
                return x.field_names()
            if isinstance(x, dict):
                return list(x.keys())
            if isinstance(x, StructureObject):
                return x.field_names()
            return []

        def _methods(x):
            meta = _meta_for(x)
            if meta and meta.get("reflectable"):
                return list(meta.get("methods") or [])
            if isinstance(x, InstanceObject) and getattr(x.class_object, "reflectable", False):
                return x.class_object.method_names()
            if isinstance(x, ClassObject) and getattr(x, "reflectable", False):
                return x.method_names()
            return []

        def _has_field(x, name):
            return name in _fields(x) or (isinstance(x, dict) and name in x)

        def _has_method(x, name):
            return name in _methods(x)

        def _field(x, name):
            if isinstance(x, dict):
                return x.get(name)
            if isinstance(x, StructureObject):
                try:
                    return x.get_member(name)
                except RuntimeError:
                    return None
            if isinstance(x, InstanceObject):
                try:
                    val = x.get_member(name)
                    if isinstance(val, tuple):
                        return val[0]
                    return val
                except RuntimeError:
                    return None
            return None

        def _set_field(x, name, value):
            if isinstance(x, dict):
                x[name] = value
                return x
            if isinstance(x, StructureObject):
                x.set_member(name, value)
                return x
            if isinstance(x, InstanceObject):
                x.set_member(name, value)
                return x
            return x

        def _is_reflectable(x):
            meta = _meta_for(x)
            if meta and meta.get("reflectable"):
                return True
            if isinstance(x, StructureObject) and getattr(x, "reflectable", False):
                return True
            if isinstance(x, InstanceObject) and getattr(x.class_object, "reflectable", False):
                return True
            if isinstance(x, ClassObject) and getattr(x, "reflectable", False):
                return True
            return False

        from Interpreter.Runtime import (
            StructureObject,
            InstanceObject,
            ClassObject,
            FunctionObject,
            BaseObject,
        )

        def _reflect_call(recv, name, args=None):
            """Dynamic call: map[name](…) or instance.method(…)."""
            if args is None:
                args = []
            if not isinstance(args, list):
                args = [args]
            name_s = str(name) if name is not None else ""

            # 1) Map of functions (plugin table)
            if isinstance(recv, dict):
                if name_s not in recv:
                    raise RuntimeError(f"reflect.call: map has no key '{name_s}'")
                fn = recv[name_s]
                if isinstance(fn, FunctionObject):
                    return self._call_function(fn, args)
                if callable(fn) and not isinstance(fn, BaseObject):
                    return fn(*args)
                raise RuntimeError(f"reflect.call: map['{name_s}'] is not callable")

            # 2) Class instance method
            if isinstance(recv, InstanceObject):
                try:
                    member = recv.get_member(name_s)
                except RuntimeError as e:
                    raise RuntimeError(f"reflect.call: {e}") from e
                if isinstance(member, tuple):
                    method, defining_class = member
                    if isinstance(method, FunctionObject):
                        bound = self._bind_method(recv, method, defining_class)
                        return self._call_function(bound, args)
                if isinstance(member, FunctionObject):
                    return self._call_function(member, args)
                raise RuntimeError(
                    f"reflect.call: '{name_s}' is not a method on {recv.class_object.name}"
                )

            # 3) Class type: unbound method not supported for call with self omitted
            raise RuntimeError(
                f"reflect.call: unsupported receiver type {type(recv).__name__}"
            )

        def _reflect_apply(fn, args=None):
            if args is None:
                args = []
            if not isinstance(args, list):
                args = [args]
            if isinstance(fn, FunctionObject):
                return self._call_function(fn, args)
            if callable(fn):
                return fn(*args)
            raise RuntimeError("reflect.apply: not a function")

        reflect_obj = BuiltinCapability("reflect", {
            "type_name": _type_name_of,
            "fields": _fields,
            "methods": _methods,
            "has_field": _has_field,
            "has_method": _has_method,
            "field": _field,
            "set_field": _set_field,
            "is_reflectable": _is_reflectable,
            "register_type": lambda n, f, m: _reflect_register_type(n, f, m, True),
            "call": _reflect_call,
            "apply": _reflect_apply,
        })
        self.global_environment.define("__builtin_reflect", reflect_obj, mutable=False, type="ReflectCapability")

        # Register 'vm' capability
        def _vm_run_file(path):
            if not path or not os.path.exists(path):
                return None
            if os.path.exists("./bin/zen"):
                import subprocess
                proc = subprocess.run(["./bin/zen", path], capture_output=True, text=True)
                out = proc.stdout.strip()
                if out:
                    try:
                        return int(out)
                    except ValueError:
                        return out
                return 0
            return None

        vm_obj = BuiltinCapability("vm", {
            "run_file": _vm_run_file,
            "run_bytecode": _vm_run_file,
            "run": _vm_run_file,
        })
        self.global_environment.define("__builtin_vm", vm_obj, mutable=False, type="VMCapability")
        self.global_environment.define("vm", vm_obj, mutable=False, type="VMCapability")
        self.global_environment.define("VM", vm_obj, mutable=False, type="VMCapability")

        # Register FFI capability
        import ctypes, ctypes.util
        def _ffi_load(path):
            raw = str(path).strip("<>\"'")
            if raw.endswith(".h"): raw = raw[:-2]
            if "/" in raw: raw = raw.split("/")[-1]
            cdll = None
            if "math" in raw:
                try: cdll = ctypes.CDLL(ctypes.util.find_library("m") or "libm.so.6")
                except Exception: pass
            if not cdll:
                try: cdll = ctypes.CDLL(None)
                except Exception: pass
            if not cdll:
                try: cdll = ctypes.CDLL(ctypes.util.find_library("c") or "libc.so.6")
                except Exception: pass
            return {"__handle": cdll, "__path": path, "__is_extern_module": True}

        def _ffi_symbol(handle_obj, name, ret_type=None):
            cdll = handle_obj.get("__handle") if isinstance(handle_obj, dict) else None
            fn = getattr(cdll, name, None) if cdll else None
            if fn is None:
                try: fn = getattr(ctypes.CDLL(None), name)
                except Exception: pass
            if fn is None: return None
            def wrapper(*args):
                c_args = []
                for a in args:
                    if isinstance(a, str): c_args.append(a.encode("utf-8"))
                    elif isinstance(a, bool): c_args.append(int(a))
                    elif isinstance(a, float): c_args.append(ctypes.c_double(a))
                    else: c_args.append(a)
                if name in ("sqrt", "pow", "sin", "cos", "tan", "exp", "log"):
                    fn.restype = ctypes.c_double
                elif name in ("getenv", "strerror"):
                    fn.restype = ctypes.c_char_p
                res = fn(*c_args)
                if isinstance(res, bytes): return res.decode("utf-8")
                return res
            return wrapper

        def _ffi_call(fn, args, ret_type=None):
            if callable(fn):
                return fn(*(args if isinstance(args, list) else [args]))
            return None

        def _ffi_close(handle_obj):
            return 0

        def _ffi_error():
            return None

        def _ffi_resolve(name):
            try:
                fn = getattr(ctypes.CDLL(None), name)
            except Exception:
                return None
            def wrapper(*args):
                c_args = []
                for a in args:
                    if isinstance(a, str): c_args.append(a.encode("utf-8"))
                    elif isinstance(a, bool): c_args.append(int(a))
                    elif isinstance(a, float): c_args.append(ctypes.c_double(a))
                    else: c_args.append(a)
                if name in ("sqrt", "pow", "sin", "cos", "tan", "exp", "log"):
                    fn.restype = ctypes.c_double
                elif name in ("getenv", "strerror"):
                    fn.restype = ctypes.c_char_p
                res = fn(*c_args)
                if isinstance(res, bytes): return res.decode("utf-8")
                return res
            return wrapper

        ffi_obj = BuiltinCapability("ffi", {
            "load": _ffi_load,
            "open": _ffi_load,
            "symbol": _ffi_symbol,
            "sym": _ffi_symbol,
            "call": _ffi_call,
            "close": _ffi_close,
            "error": _ffi_error,
            "resolve": _ffi_resolve,
        })
        self.global_environment.define("__builtin_ffi", ffi_obj, mutable=False, type="FFICapability")
        self.global_environment.define("ffi", ffi_obj, mutable=False, type="FFICapability")
        self.global_environment.define("FFI", ffi_obj, mutable=False, type="FFICapability")

        # Register 'term' capability
        def _term_color(fg=None, bg=None):
            colors = {
                "black": 0, "red": 1, "green": 2, "yellow": 3, "blue": 4, "magenta": 5, "cyan": 6, "white": 7
            }
            code = ""
            if fg in colors:
                code += f"\033[3{colors[fg]}m"
            if bg in colors:
                code += f"\033[4{colors[bg]}m"
            if code:
                print(code, end="")
            return None
        
        def _term_size():
            try:
                size = os.get_terminal_size()
                return {"width": size.columns, "height": size.lines}
            except:
                return {"width": 80, "height": 24}

        def _term_paint_canvas(canvas):
            """Fast interpret paint: color on change, one move/row, one flush."""
            if not isinstance(canvas, dict):
                return None
            w = int(canvas.get("width") or 0)
            h = int(canvas.get("height") or 0)
            buf = canvas.get("buffer") or []
            fg_buf = canvas.get("fg_buffer") or []
            bg_buf = canvas.get("bg_buffer") or []
            colors = {
                "black": 0, "red": 1, "green": 2, "yellow": 3,
                "blue": 4, "magenta": 5, "cyan": 6, "white": 7,
            }

            def apply_color(fg, bg):
                code = ""
                fgs = str(fg) if fg is not None else "white"
                bgs = str(bg) if bg is not None else "black"
                bold = False
                if fgs.startswith("bright_"):
                    bold = True
                    fgs = fgs[7:]
                if bgs.startswith("bright_"):
                    bgs = bgs[7:]
                fc = colors.get(fgs)
                bc = colors.get(bgs)
                if bold and fc is not None:
                    code += f"\033[1;3{fc}m"
                elif fc is not None:
                    code += f"\033[3{fc}m"
                if bc is not None:
                    code += f"\033[4{bc}m"
                if code:
                    print(code, end="")

            out = []
            for y in range(min(h, len(buf))):
                row = buf[y] if y < len(buf) else []
                fg_row = fg_buf[y] if y < len(fg_buf) else []
                bg_row = bg_buf[y] if y < len(bg_buf) else []
                out.append(f"\033[{y + 1};1H")
                last_fg = None
                last_bg = None
                n = min(w, len(row) if isinstance(row, list) else 0)
                for x in range(n):
                    ch = row[x]
                    if ch is None or ch == "":
                        ch = " "
                    else:
                        ch = str(ch)[0]
                    fg = fg_row[x] if isinstance(fg_row, list) and x < len(fg_row) else "white"
                    bg = bg_row[x] if isinstance(bg_row, list) and x < len(bg_row) else "black"
                    if fg != last_fg or bg != last_bg:
                        apply_color(fg, bg)
                        last_fg, last_bg = fg, bg
                    out.append(ch)
            out.append("\033[0m")
            print("".join(out), end="", flush=True)
            return None

        # Terminal raw mode + keys (editor / TUI support)
        _term_saved = {"tio": None, "raw": False}

        def _term_raw_enter():
            try:
                import termios
                import tty
                fd = sys.stdin.fileno()
                if not sys.stdin.isatty():
                    return False
                if not _term_saved["raw"]:
                    _term_saved["tio"] = termios.tcgetattr(fd)
                    tty.setraw(fd)
                    _term_saved["raw"] = True
                return True
            except Exception:
                return False

        def _term_raw_exit():
            try:
                import termios
                fd = sys.stdin.fileno()
                if _term_saved["raw"] and _term_saved["tio"] is not None:
                    termios.tcsetattr(fd, termios.TCSADRAIN, _term_saved["tio"])
                _term_saved["raw"] = False
            except Exception:
                pass
            print("\033[?25h\033[0m\033[?1049l", end="", flush=True)
            return None

        def _term_key(kind, name="", ch="", ctrl=False, code=0):
            return {
                "kind": kind,
                "name": name,
                "ch": ch,
                "ctrl": ctrl,
                "code": code,
            }

        def _term_raw_read(timeout_ms=None):
            import os as _os
            import select as _select
            import sys as _sys
            
            if "buf" not in _term_saved:
                _term_saved["buf"] = b""
                
            if _term_saved["buf"]:
                b = _term_saved["buf"][0:1]
                _term_saved["buf"] = _term_saved["buf"][1:]
                return b
                
            fd = _sys.stdin.fileno()
            if timeout_ms is not None:
                r, _, _ = _select.select([fd], [], [], timeout_ms / 1000.0)
                if not r:
                    return b""
            
            try:
                data = _os.read(fd, 1024)
            except Exception:
                return b""
                
            if not data:
                return b""
            b = data[0:1]
            _term_saved["buf"] = data[1:]
            return b

        def _term_parse_escape():
            def read_timeout(ms=50):
                b = _term_raw_read(ms)
                return b.decode("utf-8", errors="ignore") if b else None

            b1 = read_timeout(50)
            if not b1:
                return _term_key("special", name="escape", code=27)
            if b1 == "[":
                b2 = read_timeout(50)
                if not b2:
                    return _term_key("special", name="escape", code=27)
                
                if b2 == "<":
                    buf = ""
                    b_next = read_timeout(50)
                    while b_next and b_next not in ("M", "m"):
                        buf += b_next
                        b_next = read_timeout(50)
                    if b_next in ("M", "m"):
                        parts = buf.split(";")
                        if len(parts) == 3:
                            try:
                                cb = int(parts[0])
                                cx = int(parts[1])
                                cy = int(parts[2])
                                is_release = (b_next == "m") or ((cb & 3) == 3)
                                return _term_key("mouse", name="mouse", code=cb, ch=f"{cx},{cy},{1 if is_release else 0}")
                            except ValueError:
                                pass
                    return _term_key("special", name="unknown")

                arrows = {"A": "up", "B": "down", "C": "right", "D": "left", "H": "home", "F": "end"}
                if b2 in arrows:
                    return _term_key("special", name=arrows[b2])
                if b2 and b2.isdigit():
                    num = int(b2)
                    b3 = read_timeout(50)
                    while b3 and b3.isdigit():
                        num = num * 10 + int(b3)
                        b3 = read_timeout(50)
                    if b3 == "~":
                        m = {1: "home", 3: "delete", 4: "end", 5: "pageup", 6: "pagedown", 7: "home", 8: "end"}
                        if num in m:
                            return _term_key("special", name=m[num])
                return _term_key("special", name="unknown")
            return _term_key("special", name="escape", code=27)

        def _term_read_key():
            b = _term_raw_read(None)
            if not b:
                return _term_key("none", name="none")
            c = b[0]
            ch = b.decode("utf-8", errors="ignore")
            
            if c == 27:
                return _term_parse_escape()
            if c in (127, 8):
                return _term_key("special", name="backspace", code=c)
            if c in (13, 10):
                return _term_key("special", name="enter", code=c)
            if c == 9:
                return _term_key("special", name="tab", code=c)
            if 1 <= c <= 26:
                return _term_key("special", name=f"ctrl_{chr(ord('a') + c - 1)}", ctrl=True, code=c)
            if 32 <= c < 127:
                return _term_key("char", ch=ch, code=c)
            # handle multi-byte utf-8 (which would be split by our 1-byte read if we didn't buffer)
            # wait, os.read(fd, 1024) reads everything available! 
            # So if it was utf-8, it's in buf. But _term_raw_read returns 1 byte.
            # For utf-8, we might need to read more bytes to form a char.
            # But for now, returning unknown for > 127 is safe enough for basic editors.
            if c >= 128:
                # simple utf-8 assembly
                if (c & 0xE0) == 0xC0:
                    b += _term_raw_read(10)
                elif (c & 0xF0) == 0xE0:
                    b += _term_raw_read(10)
                    b += _term_raw_read(10)
                elif (c & 0xF8) == 0xF0:
                    b += _term_raw_read(10)
                    b += _term_raw_read(10)
                    b += _term_raw_read(10)
                ch = b.decode("utf-8", errors="ignore")
                return _term_key("char", ch=ch, code=c)
                
            return _term_key("special", name="unknown", code=c)

        def _term_poll_key(timeout_ms=0):
            try:
                ms = float(timeout_ms) if timeout_ms is not None else 0.0
            except Exception:
                ms = 0.0
            
            if "buf" in _term_saved and _term_saved["buf"]:
                return _term_read_key()
                
            import select, sys as _sys
            r, _, _ = select.select([_sys.stdin.fileno()], [], [], max(0.0, ms) / 1000.0)
            if not r:
                return _term_key("none", name="none")
            return _term_read_key()

        term_obj = TermCapability("term", {
            "clear": lambda: print("\033[2J\033[H", end="", flush=True),
            "move": lambda x, y: print(f"\033[{y};{x}H", end="", flush=True),
            "color": _term_color,
            "reset": lambda: print("\033[0m", end="", flush=True),
            "get_size": _term_size,
            "alt_screen_enter": lambda: print("\033[?1049h", end="", flush=True),
            "alt_screen_exit": lambda: print("\033[?1049l", end="", flush=True),
            "raw_enter": _term_raw_enter,
            "raw_exit": _term_raw_exit,
            "mouse_enable": lambda: print("\033[?1000h\033[?1006h", end="", flush=True),
            "mouse_disable": lambda: print("\033[?1000l\033[?1006l", end="", flush=True),
            "is_tty": lambda: sys.stdin.isatty(),
            "hide_cursor": lambda: print("\033[?25l", end="", flush=True),
            "show_cursor": lambda: print("\033[?25h", end="", flush=True),
            "clear_eol": lambda: print("\033[K", end="", flush=True),
            "write": lambda t: print(t if t is not None else "", end="", flush=False),
            "flush": lambda: sys.stdout.flush(),
            "paint_canvas": _term_paint_canvas,
            "read_key": _term_read_key,
            "poll_key": _term_poll_key,
        })
        self.global_environment.define("__builtin_term", term_obj, mutable=False, type="TermCapability")

        # Register 'regex' capability
        regex_obj = BuiltinCapability("regex", {
            "match": lambda pattern, string: re.match(pattern, string) is not None,
            "search": lambda pattern, string: re.search(pattern, string) is not None,
            "replace": lambda pattern, repl, string: re.sub(pattern, repl, string),
            "split": lambda pattern, string: re.split(pattern, string),
            "find_all": lambda pattern, string: re.findall(pattern, string),
        })
        self.global_environment.define("__builtin_regex", regex_obj, mutable=False, type="RegexCapability")
 
        # Register 'set' capability
        set_obj = SetCapability("set", {
            "from_list": lambda l: set(l),
            "to_list": lambda s: list(s),
            "add": lambda s, v: s.add(v),
            "has": lambda s, v: v in s,
        })
        self.global_environment.define("__builtin_set", set_obj, mutable=False, type="SetCapability")
 
        # Register 'json' capability
        json_obj = SysCapability("json", {
            "parse": lambda s: json.loads(s),
            "stringify": lambda v: json.dumps(v),
        })
        self.global_environment.define("__builtin_json", json_obj, mutable=False, type="JSONCapability")
        self.global_environment.define("json", json_obj, mutable=False, type="JSONCapability")
 
        # Register 'random' capability
        class RNGObject(BuiltinCapability):
            def __init__(self, seed_val):
                self.rng = py_random.Random(seed_val)
                super().__init__("RNG", {
                    "next": lambda: self.rng.random(),
                    "integer": lambda min_val, max_val: self.rng.randint(min_val, max_val),
                    "decimal": lambda min_val, max_val: self.rng.uniform(min_val, max_val),
                    "range": lambda min_val, max_val: self.rng.randint(min_val, max_val) if isinstance(min_val, int) and isinstance(max_val, int) else self.rng.uniform(min_val, max_val),
                })
        
        random_obj = RandomCapability("random", {
            "seed": lambda s: RNGObject(s),
            "integer": lambda min_val, max_val: py_random.randint(min_val, max_val),
            "decimal": lambda min_val, max_val: py_random.uniform(min_val, max_val),
            "range": lambda min_val, max_val: py_random.randint(min_val, max_val) if isinstance(min_val, int) and isinstance(max_val, int) else py_random.uniform(min_val, max_val),
        })
        self.global_environment.define("__builtin_random", random_obj, mutable=False, type="RandomCapability")
        # Networking
        def _net_socket(family_str, type_str):
            family = socket.AF_INET
            if family_str == "AF_INET6": family = socket.AF_INET6
            elif family_str == "AF_UNIX": family = socket.AF_UNIX
            
            sock_type = socket.SOCK_STREAM
            if type_str == "SOCK_DGRAM": sock_type = socket.SOCK_DGRAM
            
            sock = socket.socket(family, sock_type)
            
            def _sock_connect(host, port):
                sock.connect((host, port))
            
            def _sock_send(data):
                if isinstance(data, str):
                    sock.send(data.encode("utf-8"))
                else:
                    sock.send(bytes(data))
            
            def _sock_recv(bufsize):
                return sock.recv(bufsize).decode("utf-8")
                
            def _sock_close():
                sock.close()
                
            return SocketInstance("Socket", {
                "connect": _sock_connect,
                "send": _sock_send,
                "recv": _sock_recv,
                "close": _sock_close
            })

        def _net_http_request(url, method="GET", body=None, headers=None):
            if headers is None or headers is False:
                headers = {}
            if not isinstance(headers, dict):
                headers = {}
            method = method if method else "GET"
            # file:// — offline dual-path parity with native curl path
            url_s = str(url) if url is not None else ""
            if url_s.startswith("file:"):
                try:
                    path = url_s[5:]
                    if path.startswith("///"):
                        path = path[2:]  # file:///tmp/x -> /tmp/x
                    elif path.startswith("//"):
                        # file://localhost/tmp or file://host/path
                        rest = path[2:]
                        if "/" in rest:
                            rest = rest[rest.index("/"):]
                        path = rest
                    with open(path, "rb") as f:
                        data = f.read().decode("utf-8", errors="replace")
                    return {"status": 200, "body": data, "headers": {}}
                except Exception as e:
                    return {"status": -1, "body": str(e), "headers": {}}

            hdrs = {str(k): str(v) for k, v in headers.items()}
            req = urllib.request.Request(url_s, method=str(method), headers=hdrs)
            if body:
                if isinstance(body, str):
                    req.data = body.encode("utf-8")
                else:
                    req.data = bytes(body)

            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    return {
                        "status": response.status,
                        "body": response.read().decode("utf-8", errors="replace"),
                        "headers": dict(response.headers),
                    }
            except urllib.error.HTTPError as e:
                try:
                    err_body = e.read().decode("utf-8", errors="replace")
                except Exception:
                    err_body = str(e)
                return {
                    "status": e.code,
                    "body": err_body,
                    "headers": dict(e.headers) if e.headers else {},
                }
            except Exception as e:
                return {
                    "status": -1,
                    "body": str(e),
                    "headers": {},
                }

        self.global_environment.define("__builtin_net", NetCapability("net", {
            "socket": _net_socket,
            "http_request": _net_http_request
        }))

        # Crypto
        def _crypto_hash(algo, data):
            h = hashlib.new(algo)
            if isinstance(data, str):
                h.update(data.encode("utf-8"))
            else:
                h.update(bytes(data))
            return h.hexdigest()
            
        def _crypto_base64_encode(data):
            if isinstance(data, str):
                return base64.b64encode(data.encode("utf-8")).decode("utf-8")
            return base64.b64encode(bytes(data)).decode("utf-8")
            
        def _crypto_base64_decode(data):
            return base64.b64decode(data).decode("utf-8")

        self.global_environment.define("__builtin_crypto", CryptoCapability("crypto", {
            "hash": _crypto_hash,
            "b64encode": _crypto_base64_encode,
            "b64decode": _crypto_base64_decode
        }))

        # Signal
        import signal as py_signal
        
        def _signal_handle(signum, fn):
            def handler(sig, frame):
                self._call_function(fn, [sig])
            try:
                py_signal.signal(signum, handler)
                return True
            except:
                return False

        def _signal_ignore(signum):
            try:
                py_signal.signal(signum, py_signal.SIG_IGN)
                return True
            except:
                return False

        def _signal_default(signum):
            try:
                py_signal.signal(signum, py_signal.SIG_DFL)
                return True
            except:
                return False

        signal_obj = BuiltinCapability("signal", {
            "handle": _signal_handle,
            "ignore": _signal_ignore,
            "restore_default": _signal_default,
            "SIGINT": py_signal.SIGINT,
            "SIGTERM": py_signal.SIGTERM,
            "SIGHUP": py_signal.SIGHUP if hasattr(py_signal, "SIGHUP") else 1,
            "SIGQUIT": py_signal.SIGQUIT if hasattr(py_signal, "SIGQUIT") else 3,
            "SIGKILL": py_signal.SIGKILL if hasattr(py_signal, "SIGKILL") else 9,
        })
        self.global_environment.define("__builtin_signal", signal_obj, mutable=False, type="BuiltinCapability")

