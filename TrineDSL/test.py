from .parser import parse_program
from .interp import eval_program
from .interp import Env


def main():
    src = """
        trit A, B, S, C;

        A = -1;
        B = +1;
        S = TSUM(A, B);
        C = TCARRY(A, B);
    """
    prog = parse_program(src)
    env = eval_program(prog, Env())
    print(env.vars)


if __name__ == "__main__":
    main()
