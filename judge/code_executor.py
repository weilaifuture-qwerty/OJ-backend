import os
import tempfile
import subprocess
import signal
from typing import Dict, Optional

class CodeExecutor:
    def __init__(self, language: str, code: str, input_data: str, time_limit: int = 5, memory_limit: int = 256):
        self.language = language
        self.code = code
        self.input_data = input_data
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.temp_dir = None
        self.source_file = None
        self.executable = None

    def _get_compile_command(self) -> Optional[list]:
        if self.language == 'C++':
            return ['g++', '-std=c++11', '-O2', self.source_file, '-o', self.executable]
        elif self.language == 'C':
            return ['gcc', '-std=c11', '-O2', self.source_file, '-o', self.executable]
        elif self.language == 'Python':
            return None
        return None

    def _get_run_command(self) -> list:
        if self.language == 'Python':
            return ['python3', self.source_file]
        return [f'./{os.path.basename(self.executable)}']

    def _write_source_file(self):
        extensions = {
            'C++': '.cpp',
            'C': '.c',
            'Python': '.py'
        }
        ext = extensions.get(self.language, '.txt')
        self.source_file = os.path.join(self.temp_dir, f'source{ext}')
        with open(self.source_file, 'w') as f:
            f.write(self.code)

    def _compile(self) -> Optional[str]:
        compile_cmd = self._get_compile_command()
        if not compile_cmd:
            return None

        try:
            process = subprocess.run(
                compile_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            if process.returncode != 0:
                return process.stderr.decode()
        except subprocess.TimeoutExpired:
            return "Compilation timeout"
        except Exception as e:
            return str(e)
        return None

    def _run(self) -> Dict:
        run_cmd = self._get_run_command()
        try:
            process = subprocess.Popen(
                run_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )

            try:
                stdout, stderr = process.communicate(
                    input=self.input_data.encode(),
                    timeout=self.time_limit
                )
                return {
                    'output': stdout.decode(),
                    'error': stderr.decode(),
                    'exit_code': process.returncode
                }
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                return {
                    'output': '',
                    'error': f'Time limit exceeded ({self.time_limit}s)',
                    'exit_code': -1
                }
        except Exception as e:
            return {
                'output': '',
                'error': str(e),
                'exit_code': -1
            }

    def execute(self) -> Dict:
        self.temp_dir = tempfile.mkdtemp()
        try:
            self._write_source_file()
            self.executable = os.path.join(self.temp_dir, 'program')

            compile_error = self._compile()
            if compile_error:
                return {
                    'output': '',
                    'error': compile_error,
                    'exit_code': -1
                }

            return self._run()
        finally:
            # Cleanup
            if self.temp_dir and os.path.exists(self.temp_dir):
                for file in os.listdir(self.temp_dir):
                    try:
                        os.remove(os.path.join(self.temp_dir, file))
                    except:
                        pass
                os.rmdir(self.temp_dir) 