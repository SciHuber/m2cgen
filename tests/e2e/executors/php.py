import os

from m2cgen import assemblers, interpreters
from tests import utils
from tests.e2e.executors.base import BaseExecutor

EXECUTOR_CODE_TPL = """
<?php
$inputArray = array();
for ($i = 1; $i < $argc; ++$i) {{
    $inputArray[] = floatval($argv[$i]);
}}

require '{model_file}.php';

$res = score($inputArray);

{print_code}
"""

PRINT_SCALAR = """
echo($res);
"""

PRINT_VECTOR = """
echo(implode(" ", $res));
"""


class PhpExecutor(BaseExecutor):

    def __init__(self, model):
        self.model_name = "model"
        self.model = model
        self.interpreter = interpreters.PhpInterpreter()

        assembler_cls = assemblers.get_assembler_cls(model)
        self.model_ast = assembler_cls(model).assemble()

        self.executor_name = "score"

        self.script_path = None

    def predict(self, X):
        exec_args = [
            "php",
            "-f",
            self.script_path,
            "--",
            *map(utils.format_arg, X)
        ]
        return utils.predict_from_commandline(exec_args)

    def prepare(self):
        if self.model_ast.output_size > 1:
            print_code = PRINT_VECTOR
        else:
            print_code = PRINT_SCALAR
        executor_code = EXECUTOR_CODE_TPL.format(
            model_file=self.model_name,
            print_code=print_code)

        self.script_path = os.path.join(self._resource_tmp_dir, f"{self.executor_name}.php")
        with open(self.script_path, "w") as f:
            f.write(executor_code)

        model_code = self.interpreter.interpret(self.model_ast)
        model_file_name = os.path.join(self._resource_tmp_dir, f"{self.model_name}.php")
        with open(model_file_name, "w") as f:
            f.write(model_code)
