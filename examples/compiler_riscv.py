import tvm
import tvm.micro


def targetIsRISCV(target):
    return target.attrs["mcpu"] == "rv32gc"


class Compiler_RISCV(tvm.micro.DefaultCompiler):
    def _autodetect_toolchain_prefix(self, target):
        if targetIsRISCV(target):
            return "/usr/local/research/projects/SystemDesign/tools/riscv/current/bin/riscv64-unknown-elf-"

        return super(Compiler_RISCV, self)._autodetect_toolchain_prefix(target)

    def _defaults_from_target(self, target):
        opts = super(Compiler_RISCV, self)._defaults_from_target(target)
        if targetIsRISCV(target):
            opts = [opt.replace("mcpu", "march") for opt in opts]
            opts.append("-mabi=ilp32d")

        return opts
