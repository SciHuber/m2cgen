import os
import subprocess

from m2cgen import assemblers, interpreters
from tests import utils
from tests.e2e.executors.base import BaseExecutor

EXECUTOR_CODE_TPL = """
package main

import (
    "fmt"
    "os"
    "strconv"
)

{model_code}

func main() {{
    input := make([]float64, 0, len(os.Args)-1)
    for _, s := range os.Args[1:] {{
        f, _ := strconv.ParseFloat(s, 64)
        input = append(input, f)
    }}

    {print_code}
}}
"""

EXECUTE_AND_PRINT_SCALAR = """
    fmt.Printf("%f\\n", score(input))
"""

EXECUTE_AND_PRINT_VECTOR = """
    result := score(input)

    for _, v := range result {
        fmt.Printf("%f ", v)
    }
"""


class GoExecutor(BaseExecutor):

    def __init__(self, model):
        self.model_name = "score"
        self.model = model
        self.interpreter = interpreters.GoInterpreter()

        assembler_cls = assemblers.get_assembler_cls(model)
        self.model_ast = assembler_cls(model).assemble()

        self.exec_path = None

    def predict(self, X):
        exec_args = [self.exec_path, *map(utils.format_arg, X)]
        return utils.predict_from_commandline(exec_args)

    def prepare(self):
        if self.model_ast.output_size > 1:
            print_code = EXECUTE_AND_PRINT_VECTOR
        else:
            print_code = EXECUTE_AND_PRINT_SCALAR

        executor_code = EXECUTOR_CODE_TPL.format(
            model_code=self.interpreter.interpret(self.model_ast),
            print_code=print_code)

        file_name = os.path.join(self._resource_tmp_dir, f"{self.model_name}.go")
        with open(file_name, "w") as f:
            f.write(executor_code)

        self.exec_path = os.path.join(self._resource_tmp_dir, self.model_name)
        subprocess.call([
            "go",
            "build",
            "-o",
            self.exec_path,
            file_name
        ])
