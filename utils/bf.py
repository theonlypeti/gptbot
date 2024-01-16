def bf(code, inputs):
    pc = 0
    outputstring = ""
    inputpointer = 0
    mem = [0]
    pointer = 0
    jumppoints = []
    openbraces = 0
    i = 0
    while i != len(code):
        #print(mem)
        i += 1
        pc += 1
        char = code[i-1]
        if openbraces:
            if char == "[":
                openbraces += 1
            elif char == "]":
                openbraces -= 1
            continue
        if char == "<":
            if pointer == 0:
                mem.insert(0, 0)
            else:
                pointer -= 1

        elif char == ">":
            if pointer == len(mem)-1:
                mem.insert(len(mem)+1, 0)
            pointer += 1

        elif char == "+":
            mem[pointer] = (mem[pointer]+1) % 256

        elif char == "-":
            mem[pointer] = (mem[pointer]-1) % 256

        elif char == "[":
            if mem[pointer] == 0:
                openbraces += 1
            else:
                jumppoints.append(i)

        elif char == "]":
            if mem[pointer] == 0:
                jumppoints.pop()
            else:
                i = jumppoints[-1]

        elif char == ",":
            mem[pointer] = ord(inputs[inputpointer])
            inputpointer += 1
        elif char == ".":
            outputstring += chr(mem[pointer])
        else:
            continue
        
        if pc > 10000000:
            raise MaxIterationLimitExceeded()

    print(f"brainfuck program counter: {pc}")
    return outputstring


class MaxIterationLimitExceeded(Exception):
    def __init__(self):
        super().__init__("Execution stopped because the iteration limit has been exceeded.")


if __name__ == "__main__":
    print(bf(",.", "6"))
    print(bf("+[-->-[>>+>-----<<]<--<---]>-.>>>+.>>..+++[.>]<<<<.+++.------.<<-.>>>>+.",""))
    
#>++++++++++>+>+[[+++++[>++++++++<-]>.<++++++[>--------<-]+<<<]>.>>[[-]<[>+<-]>>[<<+>+>-]<[>+<-[>+<-[>+<-[>+<-[>+<-[>+<-[>+<-[>+<-[>+<-[>[-]>+>+<<<-[>+<-]]]]]]]]]]]+>>>]<<<]
        
        
        
        
            
