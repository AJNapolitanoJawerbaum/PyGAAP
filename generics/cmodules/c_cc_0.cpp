// For CPython
#include <Python.h>
#include <string>
#include <iostream>
using namespace std;

static bool ws(char ch){
	return (
		ch == '\r' || ch == '\n' || ch == '\t' || ch == '\v' || ch == '\f' ||
		ch == '\\' || ch == ' '
	);
}

// actual function
char* normalize_ws_process_single(char* text, char* str_bld){
	// const string WSCHARS[15] = {
	// 	"\u1680", "\u2000", "\u2001", "\u2002", "\u2003",
	// 	"\u2004", "\u2005", "\u2006", "\u2007", "\u2008",
	// 	"\u2009", "\u200a", "\u202f", "\u205f", "\u3000"
	// }
	//char str_bld[strlen(text)];
	int new_len = 0;
	char last_char = ' ';
	int i = 0;
	while (*(text+i) != '\0'){
		if (ws(last_char) && ws(*(text+i))){
			// check for single-byte ws chars
			i++;
			continue;
		}

		if (ws(*(text+i))){
			str_bld[new_len] = ' ';
		} else {
			str_bld[new_len] = *(text+i);
		}
		last_char = *(text+i);
		new_len ++;
		i++;
	}
	if (str_bld[new_len-1] == ' '){
		str_bld[new_len-1] = '\0';
	} else {
		str_bld[new_len] = '\0';
	}
	return str_bld;
}

// interface with python. This is what Python calls first after the setup
static PyObject* normalize_ws_ps(PyObject *self, PyObject *args){
	//vars the py function passes in
	char* text;
	// parse python function args
	if (!PyArg_ParseTuple(args, "s", &text))
		return NULL;

	// do stuff
	char str_bld[strlen(text)];
	char* out_text = normalize_ws_process_single(text, str_bld);

	return Py_BuildValue("s", out_text);
}

// declares a python function
static PyMethodDef normalize_methods[] = {
	{
		"normalize_ws_process_single", // python name
		normalize_ws_ps, // corresponding C name.
		// should be the one that has the PyObject *self, PyObject *args sig.
		METH_VARARGS,
		"Normalize whitespace (text)"
	}, {NULL, NULL, 0, NULL}
};

// declares this python module
static struct PyModuleDef c_cc_0 = {
	PyModuleDef_HEAD_INIT,
	"c_cc_0",
	"Canonicizers implemented in C/C++",
	-1,
	normalize_methods
};

PyMODINIT_FUNC PyInit_c_cc_0(void){
	return PyModule_Create(&c_cc_0);
}
