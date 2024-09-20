import re

class Node:
    def __init__(self, type_value, value=None):
        self.type_value = type_value  # 'CONST', 'TEMP', etc.
        self.value = value            # 'X', 'Y', etc.
        self.children = []
        self.parent = None
        self.cost = None
        self.padrao = []
        self.padrao_root = False
        self.tile_cost = None
        self.padrao_id = None
        self.pattern_instruction = None

    def add_child(self, child):
        self.children.append(child)
    
    def get_left(self):
        return self.children[0]
    def get_right(self):
        return self.children[1]

    def __repr__(self, level=0):
        ret = "\t" * level + f"{self.type_value}"
        if self.value is not None:
            ret += f" ({self.value})"
        ret += "\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret

def parse_expression(expression):
    # Remove parênteses extras e espaços
    expression = expression.replace('(', ' ( ').replace(')', ' ) ').replace(',', ' , ')
    tokens = expression.split()
    stack = []
    TKN_PATTERN = r'(MOVE|MEM|\+|\-|\*|\/)'  # Padrão de "tokens"
    NTKN_PATTERN = r'\(|\)|\,'
    
    i = 0 
    while i < len(tokens):
        token = tokens[i]
        if token == ')':
            # Pop until '(' is encountered
            temp_stack = []
            while stack and stack[-1] != '(':
                temp_stack.append(stack.pop())
            if stack and stack[-1] == '(':
                stack.pop()  # Remove '('
            # Create a node for the operator
            if temp_stack:
                operator = stack.pop()  # O operador é o último item no stack
                node = Node(operator.type_value)  # Cria o nó para o operador
                for child in reversed(temp_stack):
                    node.add_child(child)
                stack.append(node)
        elif token == '(':
            stack.append(token)
        elif token == ',':
            # Ignora a vírgula, não adiciona ao stack
            pass
        elif re.match(r'(CONST|TEMP)', token):
            # O próximo token deve ser o valor
            if i + 1 < len(tokens) and not re.match(TKN_PATTERN, tokens[i + 1]):
                type_value = token
                value = tokens[i + 1]
                stack.append(Node(type_value, value))
                i += 1  # Pular o próximo token, pois é parte do nó atual
            else:
                # Trata casos onde não há valor
                stack.append(Node(token))
        elif re.match(TKN_PATTERN, token):
            # Se for um operador, adiciona como um Node
            stack.append(Node(token))
        else:
            # Cria um nó para outros operandos
            type_value = token
            value = tokens[i]
            stack.append(Node(type_value, value))

        i += 1

    return stack[0] if stack else None


def print_tree(node, prefix="", is_last=True):
    if node is None:
        return
    
    # Determine o prefixo para o nó atual
    if is_last:
        print(f"{prefix}└── {node.type_value}", end="")
        new_prefix = prefix + "    "
    else:
        print(f"{prefix}├── {node.type_value}", end="")
        new_prefix = prefix + "│   "
    
    # Adiciona o valor do nó, se aplicável
    if node.type_value in ["CONST", "TEMP"] and node.value is not None:
        print(f" ({node.value})")
    else:
        print()
    
    # Print children
    for i, child in enumerate(node.children):
        print_tree(child, new_prefix, i == len(node.children) - 1)

COSTS = {
    "+": 1,
    "*": 1,
    "/": 1,
    "TEMP": 0,
    "-": 1,
    "LOAD": 1,
    "STORE": 1,
    "MOVE": 2,
    "CONST": 1,
    "MEM": 1
}


PATTERNS = {
        1: "TEMP r{i}",
        2: "ADD r{i} <- r{j} + r{k}",
        3: "MUL r{i} <- r{j} * r{k}",
        4: "SUB r{i} <- r{j} - r{k}",
        5: "DIV r{i} <- r{j} / r{k}",
        6: "ADDI r{i} <- r{j} + {c}",
        7: "ADDI r{i} <- r{j} + {c}",
        8: "ADDI r{i} <- r{j} + {c}",
        9: "SUBI r{i} <- r{j} - {c}",
        10: "LOAD r{i} <- M[r{j} + {c}]",
        11: "LOAD r{i} <- M[r{j} + {c}]",
        12: "LOAD r{i} <- M[r{j} + {c}]",
        13: "LOAD r{i} <- M[r{j} + {c}]",
        14: "STORE M[r{j} + {c}] <- r{i}",
        15: "STORE M[r{j} + {c}] <- r{i}",
        16: "STORE M[r{j} + {c}] <- r{i}",
        17: "STORE M[r{j} + {c}] <- r{i}",
        18: "MOVEM M[r{j}] <- M[r{i}]",
    }


#criando os padrões

def sumOperator(node: Node):
    constIsFound = False
    for i in range(len(node.children)):
        if (node.children[i].type_value == "CONST"):
            tile = [node, node.children[i]]
            node.padrao = tile
            node.children[i].padrao = tile
            #padrão da raiz agora passa a ser considerado
            node.padrao_root = True
            #isso significa que o padrão do filho não irá ser considerado
            node.children[i].padrao_root = False
            node.padrao_id = 6
            constIsFound = True
        if constIsFound:
            break
    if not constIsFound:
        tile = [node]
        node.padrao_id = 2
        node.padrao = tile
        node.padrao_root = True


def minusOperator(node: Node):
    if (node.children[1].type_value == "CONST"):
        tile = [node, node.children[1]]
        node.padrao = tile
        node.children[1].padrao = tile
        #padrão da raiz agora passa a ser considerado
        node.padrao_root = True
        #isso significa que o padrão do filho não irá ser considerado
        node.children[1].padrao_root = False
        node.padrao_id = 9
    else:
        tile = [node]
        node.padrao_id = 4
        node.padrao = tile
        node.padrao_root = True


def memOperator(node: Node):
    if (node.children[0].type_value == "+"):
        #se for um addi, então eu sei que pelo menos tenho um const
        if (len(node.children[0].padrao) == 2):
            son_pattern = node.children[0].padrao
            pattern = [node, son_pattern[0], son_pattern[1]]
            node.padrao = pattern
            node.children[0].padrao = pattern
            node.padrao_root = True
            node.children[0].padrao_root = False
            node.padrao_id = 10

    elif (node.children[0].type_value == "CONST"):
        pattern = [node, node.children[0]]
        node.padrao = pattern
        node.children[0].padrao = pattern
        node.padrao_root = True
        node.children[0].padrao_root = False
        node.padrao_id = 11
    #MEM USA TEMP
    else:
        pattern = [node]
        node.padrao = pattern
        node.padrao_root = True
        node.padrao_id = 12


def moveOperator(node: Node):
    if (node.children[0].type_value == "MEM" and node.children[1].type_value != "MEM"):
        if (node.children[0].padrao_id == 10):
            tile = [node] + node.children[0].padrao 
            pattern = 14
            node.padrao_id = pattern
            node.padrao_root = True
            node.padrao = tile
            #colocando o tile em todos os nós que o compõem 
            for nodo in node.children[0].padrao:
                nodo.padrao = tile
                nodo.padrao_root = False

        elif (node.children[0].padrao_id == 11):
            tile = [node] + node.children[0].padrao
            pattern = 15
            node.padrao_id = pattern
            node.padrao_root = True
            node.padrao = tile
            #colocando o tile em todos os nós que o compõem 
            for nodo in node.children[0].padrao:
                nodo.padrao = tile
                nodo.padrao_root = False
 
        else:
            tile = [node] + node.children[0]
            pattern = 16
            node.padrao_id = pattern
            node.padrao = pattern
            node.padrao_root = True
            node.children[0].padrao_root = False

    #os dois filhos são iguais a MEM        
    else:
        tile = [node, node.children[0], node.children[1]]
        pattern = 18
        node.padrao = tile
        node.padrao_root = True
        node.padrao_id = pattern

        for nodo in node.children:
            if not nodo.children[0].padrao_root:
                percorrendo(nodo.children[0])
            nodo.padrao = tile
            nodo.padrao_root = False

def multiOperator(node: Node):
    tile = [node]
    node.padrao_id = 3
    node.padrao = tile
    node.padrao_root = True

def divOperator(node: Node):
    tile = [node]
    node.padrao_id = 5
    node.padrao = tile
    node.padrao_root = True

def const(node : Node):
    tile = [node]
    node.padrao_id = 8
    node.padrao = tile
    node.padrao_root = True

def temp(node : Node):
    tile = [node]
    node.padrao_id = 1
    node.padrao = tile
    node.padrao_root = True
            

#computo todos os custos do node associando os padrões
MEMO = {}

def computeCosts(root):
    custo = 0
    padroes = []

    def get_padroes(node):
        if node is not None:
            for child in node.children:
                get_padroes(child)
            if node.padrao_root:
                padrao = [n.type_value for n in node.padrao]
                padroes.append(padrao)

    get_padroes(root)

    for arr in padroes:
        arr_tuple = tuple(arr)  
        if arr_tuple in MEMO:
            custo += MEMO[arr_tuple]
        else:
            aux = 0
            for inst in arr:
                aux += COSTS.get(inst, 0)  
            MEMO[arr_tuple] = aux  
            custo += aux

    print(f"Custo Total = {custo}")

def percorrendo(root):
    # Função auxiliar para realizar a travessia em pós-ordem
    def post_order(node):
        if node is not None:
            # Primeiro, percorrer todos os filhos
            for child in node.children:
                post_order(child)

            if (node.type_value == "+"):
                sumOperator(node)
            elif (node.type_value == "-"):
                minusOperator(node)
            elif (node.type_value == "*"):
                multiOperator(node)
            elif (node.type_value == "/"):
                divOperator(node)
            elif (node.type_value == "MEM"):
                memOperator(node)
            elif (node.type_value == "MOVE"):
                moveOperator(node)
            elif (node.type_value == "CONST"):
                const(node)
            elif (node.type_value == "TEMP"):
                temp(node)

    post_order(root)


def verificar_nos(root):
    padroes = []

    def post_order(node):
        if node is not None:
            for child in node.children:
                post_order(child)
            if node.padrao_root:
                padrao = [n.type_value for n in node.padrao]
                print(padrao)
                padroes.append(node.padrao)
    post_order(root)
    return padroes


def codigo_equivalente(padroes):
        a = 1 
        b = 1
        c = 1
        for i in range(len(padroes)):
            for j in range(len(padroes[i])):
                if padroes[i][j].padrao_root == True:
                    node = padroes[i][0] 
                    option = padroes[i][0].padrao_id 
                    instruction = PATTERNS.get(option, "Padrão não encontrado") 
                    
                    if (option == 1): #TEMP
                        #apenas para criar um novo registrador
                        c = b
                        b = a
                        a += 1
                
                    if (option in [2, 3, 4, 5]): #ADD, SUB, MUL e DIV
                        if(node.children[0].value != None):
                            print(i+1, instruction.format(i=b, j=node.children[0].value, k=b))
                        else:
                            print(i+1, instruction.format(i=b, j=c, k=b))

                    if (option in [6, 7, 9]): #ADDI e SUBI
                        aux1 = node.children[1].value
                        aux2 = node.children[0].value
                        a+=1
                        if (option == 6 or option == 9):
                            print(i+1, instruction.format(i=b, j=aux2, c=aux1))
                        else :
                            print(i+1, instruction.format(i=b, j=aux1, c=aux2))   
                    
                    if (option == 8): # ADDI (caso especial)
                        print(i+1, instruction.format(i=b, j=0, c=node.value))
                    
                    if (option in [10, 11]): 
                        child = node.children[0]
                        aux1 = child.children[1].value
                        aux2 = child.children[0].value
                        a+=1
                        if (option == 10):  
                            print(i+1, instruction.format(i=b, j=aux2, c=aux1))
                        else :
                            print(i+1, instruction.format(i=b, j=aux1, c=aux2))  
                    
                    if (option == 12): #LOAD terceiro caso
                        child = node.children[0]
                        print(i+1, instruction.format(i=b, j=0, c=child.value))

                    if (option == 13): #LOAD quarto caso
                        print(i+1, instruction.format(i=b, j=b, c=0))

                    if (option in [14, 15]): #MOVE dois primeiros casos
                        child = node.children[0].children[0]
                        aux1 = child.children[1].value
                        aux2 = child.children[0].value
                        a+=1 
                        if (option == 14): 
                            print(i+1, instruction.format(i=b, j=aux2, c=aux1))
                        else :
                            print(i+1, instruction.format(i=b, j=aux1, c=aux2))  

                    if (option == 16): #MOVE terceiro caso
                        child = node.children[0].children[0]
                        print(i+1, instruction.format(i=b, j=0, c=child.value))

                    if (option == 17): #MOVE quarto caso
                        print(i+1, instruction.format(i=b, j=a, c=0))
                    
                    if (option == 18): #MOVEM
                        print(i+1, instruction.format(i=b, j=a))





def processar_arquivo(arquivo):
    try:
        with open(arquivo, 'r') as file:
            # Para cada linha no arquivo
            for linha in file:
                expression = linha.strip()  

                if expression:  
                    print(f"Processando a expressão: {expression}\n")

                    tree = parse_expression(expression)
                    print("1. Árvore gerada:")
                    print_tree(tree)  # Supondo que print_tree já imprime a árvore de forma adequada
                    print("\n")

                    print("2. Padroes e custo total:")
                    percorrendo(tree)  # Executa alguma operação de percurso na árvore
                    padroes = verificar_nos(tree)  # Verifica padrões nos nós da árvore
                    computeCosts(tree)  # Executa a função para computar custos
                    print("\n")

                    print("3. Código equivalente gerado:")
                    codigo_equivalente(padroes)  # Gera o código a partir dos padrões
                    print("\n\n")
    
    except FileNotFoundError:
        print(f"O arquivo {arquivo} não foi encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro: {str(e)}")

processar_arquivo('testes.txt')
