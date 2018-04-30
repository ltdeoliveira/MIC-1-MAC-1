# Dicionário que contém as instruções sem operando.
dict1 = { 'nop':    0x01,     'iadd':          0x02,    'isub':   0x05,     'iand':      0x08,
          'ior':    0x0b,     'dup':           0x0e,    'pop':    0x10,     'swap':      0x13,
          'wide':   0x28,     'ireturn':       0x6b }

# Dicionário que contém as instruções com operando(s).
dict2 = { 'goto':   0x3c,     'iftl':          0x43,    'ifeq':   0x47,     'if_icmpeq': 0x4b,  # Desvios
          'ldc_w':  0x32,     'invokevirtual': 0x55,                                            # Operando de dois bytes.
          'bipush': 0x19,     'iload':         0x1c,    'istore': 0x22,     'iinc':      0x36   # Operando de um byte.
}

labels = {}     # Dicionário que armazena as labels e suas respectivas posições (em bytes).
constants = {}  # Dicionário que armazena as constantes e suas posições de memória (em bytes).
byte_array = [] # Lista que armazena os bytes que serão adicionados ao arquivo.
error_log = ''  # String que armazena o log de erros do programa.

byte_counter = 0  # Contador global de bytes.
next_constant = 0 # Contador global de constantes.

def main():
    global byte_counter
    with open('programa.asm') as program:
        line_counter = 0 # Conta as linhas.

        for line in program:
            line_counter += 1

            sline = line.lower().split() # Separa as strings da linha em uma lista.
            
            if sline != [] and not is_comment(sline[0]):
                
                if is_label(sline[0]):
                    add_label(sline[0])
                    del sline[0]

                if is_valid_instruction(sline[0]):
                    add_instruction(sline[0])

                else:
                    add_error('invalid_instruction', line_counter)
                    
                if is_valid_operand(sline):
                    if sline[0] in dict2:
                        add_operand(sline)

                else:
                    add_error('invalid_operand', line_counter)
        
    generate_file()

# Escopo das funções.

def is_comment(string):              # Informa se uma string é um comentário.
    return string.startswith('//')

def is_label(string):                # Informa se uma string é uma label.
    return (string.startswith('l')) and (string[1:].isnumeric())

def add_label(label):                # Adiciona uma label ao vetor byte_array.
    global byte_counter
    labels[label] = byte_counter + 1

def is_valid_instruction(string):    # Informa se uma instrução é válida.
    return (string in dict1.keys()) or (string in dict2.keys())

def add_instruction(instruction):    # Adiciona o endereço de uma instrução ao byte_array.
    global byte_counter
    byte_counter += 1

    if instruction in dict1.keys():
        byte_array.append(hex(dict1[instruction]))

    else:
        byte_array.append(hex(dict2[instruction]))

def is_valid_constant(string):        # Informa se uma string é uma constante válida.
    return (len(string) > 0) and (string[0].isalpha())

def is_valid_operand(sline):         # Informa se uma linha possui operando(s) válido(s).
    if sline[0] in dict1.keys():
        return (len(sline) == 1) or (is_comment(sline[1]))
    
    elif sline[0] in dict2.keys():
        if (len(sline) > 1) and (not is_comment(sline[1])):
            
            if (sline[0] == 'goto') or (sline[0] == 'iflt') or (sline[0] == 'ifeq') or (sline[0] == 'if_icmpeq'):
                return ((len(sline) == 2) or (is_comment(sline[2]))) and (is_label(sline[1]))
            
            elif (sline[0] == 'bipush') or (sline[0] == 'ldc_w') or (sline[0] == 'invokevirtual'):
                return ((len(sline) == 2) or (is_comment(sline[2]))) and (sline[1].isnumeric())
            
            elif (sline[0] == 'iload'):
                return ((len(sline) == 2) or (is_comment(sline[2]))) and (sline[1] in constants)
            
            elif (sline[0] == 'istore'):
                return ((len(sline) == 2) or (is_comment(sline[2]))) and (is_valid_constant(sline[1]))
            
            else: # (sline == 'iinc')
                if (len(sline) > 2) and (not is_comment(sline[2])):
                    return ((len(sline) == 3) or (is_comment(sline[3]))) and (sline[1].isnumeric()) and (is_valid_constant(sline[2]))

    else:
        return False

def add_operand(sline):              # Adiciona o endereço de um operando ao byte_array.
    global byte_counter
    global next_constant
    if (sline[0] == 'goto') or (sline[0] == 'iflt') or (sline[0] == 'ifeq') or (sline[0] == 'if_icmpeq'):
        byte_array.append([sline[1], byte_counter])
        byte_counter += 2
    
    elif (sline[0] == 'bipush'):
        byte_array.append("0x{:02x}".format(int(sline[1])))
        byte_counter += 1
    
    elif (sline[0] == 'iload'):
        byte_array.append("0x{:02x}".format(constants[sline[1]]))
        byte_counter += 1
    
    elif (sline[0] == 'istore'):
        if sline[1] not in constants.keys():
            constants[sline[1]] = next_constant
            next_constant += 1
        byte_array.append("0x{:02x}".format(constants[sline[1]]))
        byte_counter += 1

    elif (sline[0] == 'ldc_w') or (sline[0] == 'invokevirtual'):
        byte_array.append("0x{:02x}".format(int(sline[1]) & 0xFF))
        byte_array.append("0x{:02x}".format(int(sline[1]) >> 8))
        byte_counter += 2
    
    else: # (sline == 'iinc')
        byte_array.append("0x{:02x}".format(int(sline[1])))
        byte_array.append("0x{:02x}".format(constants[sline[2]]))
        byte_counter += 2

def add_error(error_type, error_line): # Adiciona um erro ao log de erros.
    global error_log
    error_to_be_added = 'Line: ' + str(error_line) + 'error: ' + str(error_type) + '\n'
    error_log = error_log + error_to_be_added

def generate_file(): # Gera o arquivo final.
    global byte_array

    print (labels)
    print (byte_array)

    # for line in byte_array:
    #     if type(line) is int:
    #         print (hex(line))
    #     else:
    #         print('%s' %line)

if __name__ == "__main__":
    main()