import parsley, re, sys, os
program = ""
def print_(a):
    global program
    program = a
    # print(a)
    # print("---RUNNING------------")
    # exec(a)
    return a

# def return_instructions():

functions = {}

def prefix(l, string):
    new_l = []
    for item in l:
        new_l.append(string + item)
    return new_l

def replace_function_names(name):
    return name.replace(">=", "equal_greater_than").replace("<=", "equal_less_than").replace("=","equals").replace(">","greater").replace("<","less")

def replace_scope(name, parameters, instructions):
    new_instructions = []
    for ins in instructions:
        for param in parameters:
            ins = re.sub(r"\b{}\b".format(param), name+":"+param, ins)
        ins = re.sub(r"\breturn\b", name+":return", ins)
        # print(ins)
        new_instructions.append(ins)
    return new_instructions

def function_call(name, parameters):
    if not name in functions:
        new_parameters = []
        for param in parameters:
            if (not '\"' in param) and not param.isdigit():
                new_parameters.append("load(\"" + param + "\")")
            else:
                new_parameters.append(param)
        return replace_function_names(name) + "(" + ','.join(new_parameters) + ");"
    else:
        return_script = ""
        for i, param in enumerate(parameters):
            if (not '\"' in param) and not param.isdigit():
                return_script += "store(\"" + functions[name][0][i] + "\", load(\"" + param + "\"));\n"
            else:
                return_script += "store(\"" + functions[name][0][i] + "\", " + param + ");\n"
        return_script += '\n'.join(functions[name][1])
        # print(return_script)
        return return_script

def return_call_condition(name, parameters, prefix="if"):
    if not name in functions:
        new_parameters = []
        for param in parameters:
            if (not '\"' in param) and not param.isdigit():
                new_parameters.append("load(\"" + param + "\")")
            else:
                new_parameters.append(param)
        return prefix + " ("+replace_function_names(name) + "(" + ','.join(new_parameters) + "))"
    else:
        return_script = ""
        for i, param in enumerate(parameters):
            if (not '\"' in param) and not param.isdigit():
                return_script += "store(\"" + functions[name][0][i] + "\", load(\"" + param + "\"));\n"
            else:
                return_script += "store(\"" + functions[name][0][i] + "\", " + param + ");\n"
        return_script += '\n'.join(functions[name][1])
        return_script += "\n"+ prefix +" (any_cast<int>(load(\"" + name + ":return\")))"
        # print(return_script)
        return return_script

def transform_(instructions):
    new_instructions = []
    joined_ins = '\n'.join(instructions)
    split_ins = joined_ins.split('\n')
    for ins in split_ins:
        new_instructions.append('\t'+ins)
    return '\n'.join(new_instructions)


def store_instructions(name, parameters, instructions):
    functions[name] = (parameters, instructions)
    # print((name, parameters, instructions))

def for_condition(arg):
    if any(c.isalpha() for c in arg):
        return "load(\"" + arg + "\")"
    else:
        return "1"

def replace_call(var_name, name, parameters):

    # print("var_name: ", var_name)
    # print("name: ", name)
    # print("params: ", parameters)

    if not name in functions:
        new_parameters = []
        for param in parameters:
            if (not '\"' in param) and not param.isdigit():
                new_parameters.append("load(\"" + param + "\")")
            else:
                new_parameters.append(param)
        return "store(\"" + var_name + "\"," + replace_function_names(name) + "(" + ','.join(new_parameters) + "));"
    else:
        return_script = ""
        for i, param in enumerate(parameters):
            if (not '\"' in param) and not param.isdigit():
                return_script += "store(\"" + functions[name][0][i] + "\", load(\"" + param + "\"));\n"
            else:
                return_script += "store(\"" + functions[name][0][i] + "\", " + param + ");\n"
        return_script += '\n'.join(functions[name][1])
        return_script += "\nstore(\"" + var_name + "\", load(\"" + name + ":return\"));"

        # print(return_script)
        return return_script

x = parsley.makeGrammar("""
w = <(' ' | '\\t' | '\\n')*>

digit = anything:x ?(x in '0123456789')
letter = anything:x ?(x in 'abcdefghijklmnopqrstuvwxyz=<>_' or x in 'abcdefghijklmnopqrstuvwxyz'.upper())


IDENTIFIER = w <letter+>:ds -> str(ds)
NUMBER = (<digit+>:ds -> str(ds)
			| '-' <digit+>:ds -> '-' + str(ds)
			)
STRING = "'" (~"'" anything)*:c "'" -> 'string("' + ''.join(c) + '")'
OBJECT = IDENTIFIER | DATA
DATA = NUMBER | STRING


for_loop = (
              "for" (w IDENTIFIER | w):con "{" w statement*:a w "}" w -> "while (any_cast<int>("+ for_condition(con) + "))\\n{\\n" + transform_(a) + "\\n}"
            | "for" IDENTIFIER:a w "(" (w OBJECT)*:b w ")" w "{" w statement*:c w "}" w -> return_call_condition(a, b, "while") + "\\n{\\n" + transform_(c) + "\\n}"
            )

if_state = (
              "if" (w IDENTIFIER | w):con "{" w statement*:a w "}" w -> "if (any_cast<int>("+ for_condition(con) + "))\\n{\\n" + transform_(a) + "\\n}"
            | "if" IDENTIFIER:a w "(" (w OBJECT)*:b w ")" w "{" w statement*:c w "}" w -> return_call_condition(a, b) + "\\n{\\n" + transform_(c) + "\\n}"
            )


main = "main" w "{" w statement*:a w "}" w -> '\\n'.join(a)
call = IDENTIFIER:a w "(" (w OBJECT)*:b w ")" w -> function_call(a, b)
equals = IDENTIFIER:a w "<-" w (
                                IDENTIFIER:b w "(" (w OBJECT)*:c w ")" w -> replace_call(a, b, c)
                                | DATA:b w -> "store(\\"" + a + "\\", " + b + ");"
                                | IDENTIFIER:b w -> "store(\\"" + a + "\\", load(" + b + "));"
                                )

function_def = IDENTIFIER:a w ":" w (IDENTIFIER)*:b w "{" w (statement)*:c w "}" w -> store_instructions(a, prefix(b, a+":"), replace_scope(a,b,c))

outside_main = (
            function_def
            | main:a -> print_(a)
            )


statement = w (
            function_def
            | if_state
            | for_loop
            | call
            | equals
            )

expr = <outside_main+>:a -> a

""",
    {
        "print_":print_,
        "store_instructions":store_instructions,
        "prefix":prefix,
        "transform_":transform_,
        "function_call":function_call,
        "replace_call":replace_call,
        "replace_scope":replace_scope,
        "for_condition":for_condition,
        "return_call_condition":return_call_condition
    }
)
with open(sys.argv[1], "r") as f:
    code_ = f.read()

x(code_).expr()
print(program)

with open("main.cpp", "w") as f:
    f.write("""
#include <boost/any.hpp>
#include <iostream>
#include <map>
#include <string>
using namespace std;
using boost::any_cast;

map<string, boost::any> variables;

//taken from boost example
bool is_string(const boost::any & operand)
{
	return any_cast<string>(&operand);
}

ostream& operator<<(ostream& out, boost::any &operand) {
	if (operand.type() == typeid(int)) {
		out << any_cast<int>(operand);
	} else if (is_string(operand)) {
		out << any_cast<string>(operand);
	} else if (operand.type() == typeid(float)) {
		out << any_cast<float>(operand);
	} else if (operand.type() == typeid(double)) {
		out << any_cast<double>(operand);
	};
	return out;
}

double add(boost::any a, boost::any b)
{
	double a_;
	double b_;

	if (a.type() == typeid(int)) {
		a_ = any_cast<int>(a);
	} else if (a.type() == typeid(float)) {
		a_ = any_cast<float>(a);
	} else if (a.type() == typeid(double)) {
		a_ = any_cast<double>(a);
	};

	if (b.type() == typeid(int)) {
		b_ = any_cast<int>(b);
	} else if (b.type() == typeid(float)) {
		b_ = any_cast<float>(b);
	} else if (b.type() == typeid(double)) {
		b_ = any_cast<double>(b);
	};

	return a_ + b_;
}

double sub(boost::any a, boost::any b)
{
	double a_;
	double b_;

	if (a.type() == typeid(int)) {
		a_ = any_cast<int>(a);
	} else if (a.type() == typeid(float)) {
		a_ = any_cast<float>(a);
	} else if (a.type() == typeid(double)) {
		a_ = any_cast<double>(a);
	};

	if (b.type() == typeid(int)) {
		b_ = any_cast<int>(b);
	} else if (b.type() == typeid(float)) {
		b_ = any_cast<float>(b);
	} else if (b.type() == typeid(double)) {
		b_ = any_cast<double>(b);
	};

	return a_ * b_;
}

double mul(boost::any a, boost::any b)
{
	double a_;
	double b_;

	if (a.type() == typeid(int)) {
		a_ = any_cast<int>(a);
	} else if (a.type() == typeid(float)) {
		a_ = any_cast<float>(a);
	} else if (a.type() == typeid(double)) {
		a_ = any_cast<double>(a);
	};

	if (b.type() == typeid(int)) {
		b_ = any_cast<int>(b);
	} else if (b.type() == typeid(float)) {
		b_ = any_cast<float>(b);
	} else if (b.type() == typeid(double)) {
		b_ = any_cast<double>(b);
	};

	return a_ * b_;
}

double div(boost::any a, boost::any b)
{
	double a_;
	double b_;

	if (a.type() == typeid(int)) {
		a_ = any_cast<int>(a);
	} else if (a.type() == typeid(float)) {
		a_ = any_cast<float>(a);
	} else if (a.type() == typeid(double)) {
		a_ = any_cast<double>(a);
	};

	if (b.type() == typeid(int)) {
		b_ = any_cast<int>(b);
	} else if (b.type() == typeid(float)) {
		b_ = any_cast<float>(b);
	} else if (b.type() == typeid(double)) {
		b_ = any_cast<double>(b);
	};

	return a_ / b_;
}

bool equal_greater_than(boost::any a, boost::any b)
{
	double a_;
	double b_;

	if (a.type() == typeid(int)) {
		a_ = any_cast<int>(a);
	} else if (a.type() == typeid(float)) {
		a_ = any_cast<float>(a);
	} else if (a.type() == typeid(double)) {
		a_ = any_cast<double>(a);
	};

	if (b.type() == typeid(int)) {
		b_ = any_cast<int>(b);
	} else if (b.type() == typeid(float)) {
		b_ = any_cast<float>(b);
	} else if (b.type() == typeid(double)) {
		b_ = any_cast<double>(b);
	};

	return a_ >= b_;
}

bool equal_less_than(boost::any a, boost::any b)
{
	double a_;
	double b_;

	if (a.type() == typeid(int)) {
		a_ = any_cast<int>(a);
	} else if (a.type() == typeid(float)) {
		a_ = any_cast<float>(a);
	} else if (a.type() == typeid(double)) {
		a_ = any_cast<double>(a);
	};

	if (b.type() == typeid(int)) {
		b_ = any_cast<int>(b);
	} else if (b.type() == typeid(float)) {
		b_ = any_cast<float>(b);
	} else if (b.type() == typeid(double)) {
		b_ = any_cast<double>(b);
	};

	return a_ <= b_;
}

bool greater(boost::any a, boost::any b)
{
	double a_;
	double b_;

	if (a.type() == typeid(int)) {
		a_ = any_cast<int>(a);
	} else if (a.type() == typeid(float)) {
		a_ = any_cast<float>(a);
	} else if (a.type() == typeid(double)) {
		a_ = any_cast<double>(a);
	};

	if (b.type() == typeid(int)) {
		b_ = any_cast<int>(b);
	} else if (b.type() == typeid(float)) {
		b_ = any_cast<float>(b);
	} else if (b.type() == typeid(double)) {
		b_ = any_cast<double>(b);
	};

	return a_ > b_;
}

bool less(boost::any a, boost::any b)
{
	double a_;
	double b_;

	if (a.type() == typeid(int)) {
		a_ = any_cast<int>(a);
	} else if (a.type() == typeid(float)) {
		a_ = any_cast<float>(a);
	} else if (a.type() == typeid(double)) {
		a_ = any_cast<double>(a);
	};

	if (b.type() == typeid(int)) {
		b_ = any_cast<int>(b);
	} else if (b.type() == typeid(float)) {
		b_ = any_cast<float>(b);
	} else if (b.type() == typeid(double)) {
		b_ = any_cast<double>(b);
	};

	return a_ < b_;
}

int equals(const boost::any& a1, const boost::any& a2) {
    // cout << "compare " << *boost::unsafe_any_cast<void*>(&a1)
    //      << " with:  " << *boost::unsafe_any_cast<void*>(&a2);
    return (*boost::unsafe_any_cast<void*>(&a1)) ==
        (*boost::unsafe_any_cast<void*>(&a2));
}

void print(boost::any value)
{
	cout << value << endl;
}

string input()
{
	string a;
    getline(cin, a);
	return a;
}

void store(string var, boost::any value)
{
	variables[var] = value;
}

boost::any load(string var)
{
	return variables[var];
}

int main() {
""")

    f.write(program)
    f.write("""
return 0;
}
""")
    f.close()

os.system("g++ -std=c++14 main.cpp")
