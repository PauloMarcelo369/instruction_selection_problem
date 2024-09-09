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
            stack.append(Node(token))

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
        "ADD": 1,
        "ADDI": 1,
        "MUL": 1,
        "DIV": 1,
        "TEMP": 0,
        "SUBI": 1,
        "LOAD": 1,
        "STORE": 1,
        "MOVEM": 2,
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
# def computeCosts(node):

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
            else:
                temp(node)

    post_order(root)


def verificar_nos(root):
    
    percorrendo(root)
    def post_order(node):
        if node is not None:
            for child in node.children:
                post_order(child)
            if node.padrao_root:
                print([n.type_value for n in node.padrao])
    post_order(root)

# expression = "MOVE ( MEM ( - ( MEM ( + ( TEMP i , CONST 3 ) ) , * ( - ( TEMP x , FP ) , CONST 2 ) ) , CONST 4 ) , MEM ( / ( CONST 6 , FP ) ) )"
expression = "MOVE ( MEM ( + ( MEM ( + ( FP , CONST a ) ) , * ( TEMP i , CONST 4 ) ) ) , MEM ( + ( FP , CONST x ) ) )"
# expression = "MOVE ( MEM ( + ( CONST 2 , TEMP i ) ) , TEMP j )"
tree = parse_expression(expression)
print_tree(tree)
verificar_nos(tree)