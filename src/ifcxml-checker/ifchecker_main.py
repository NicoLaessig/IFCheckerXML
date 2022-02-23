"""
This python file validates the correctness of .ifcxml files and returns the list of
errors found (if any) via a .csv file.
For the validation check the newest ISO publicated IFC version is used: IFC4 ADD2 TC1.
"""
import argparse
from lxml import etree
import pandas as pd
import ifcheck
from ifcheck.basic import load_obj

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", type=str, help="Directory and name of the input .ifcxml file.")
parser.add_argument("-o", "--output", type=str, help="Directory of the output files.")
args = parser.parse_args()

inputfile = args.input
outputfile = args.output

#If pickle file/dictionary already created; load them up & validate the file
entity_dict = load_obj("entities")
type_dict = load_obj("types")


validation_output = pd.DataFrame(columns=["line", "id", "error_type", "error_message", "rule_name",
    "entity_type", "attribute_type", "link", "document_reference"])

if inputfile.endswith(".ifcxml"):
    parser = etree.XMLParser()
    tree = etree.parse(inputfile, parser)
    root = tree.getroot()
    for elem in root.getiterator():
        if not hasattr(elem.tag, 'find'): continue
        i = elem.tag.find('}')
        if i >= 0:
            elem.tag = elem.tag[i+1:]
else:
    print("Input file cannot be read. Please specify an .ifcxml file with IFC4 version as input.")


type_namespace = "{http://www.w3.org/2001/XMLSchema-instance}type"

Val = ifcheck.Validator(tree, entity_dict, type_dict, validation_output, type_namespace)
R = ifcheck.Rules(tree, entity_dict, type_namespace)

#Syntax check of file
#Check if (1) all IDs are unique; (2) referenced objects are valid;
#(3) all required children & attributes are given:
#(3.1) all types are correct; (3.2) formal propositions/rules are fulfilled
#print() all errors/mistakes for checking, before throwing errors

Val.unique_ids()

#Call each top element of the .ifcxml file and then iteratively call each child.
for i, current_entity in enumerate(root):
    if i > 0:
        Val.check_children(current_entity, current_entity.tag, [], [], [], [], [current_entity.tag])


Val.print_result(outputfile)
