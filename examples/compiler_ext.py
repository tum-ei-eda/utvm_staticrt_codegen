import tvm
import tvm.micro


def targetIsARM(target):
    return "mcpu" in target.attrs and target.attrs["mcpu"] == "armv6-m"
def targetIsRISCV(target):
    return "mcpu" in target.attrs and target.attrs["mcpu"] == "rv32gc"


class Compiler_Ext(tvm.micro.DefaultCompiler):
    def _autodetect_toolchain_prefix(self, target):
        if targetIsARM(target):
            return "arm-none-eabi-"
        if targetIsRISCV(target):
            return "/usr/local/research/projects/SystemDesign/tools/riscv/current/bin/riscv64-unknown-elf-"

        return super(Compiler_Ext, self)._autodetect_toolchain_prefix(target)

    def _defaults_from_target(self, target):
        opts = super(Compiler_Ext, self)._defaults_from_target(target)
        if targetIsARM(target):
            opts = [opt.replace("mcpu", "march") for opt in opts]
            opts.append("-mthumb")
            opts.append("--specs=nosys.specs")
        if targetIsRISCV(target):
            opts = [opt.replace("mcpu", "march") for opt in opts]
            opts.append("-mabi=ilp32d")

        return opts
