"""In this file, IFC Entity & Type dictionaries get generated."""
import json
import re
import pandas as pd
from .basic import save_obj

def create_dict(entity_file, type_file, save_json):
    """Takes the entity and type files as input and then creates respective dictionaries
    as .pkl files.
    Dictionaries can additionally be saved as .json files if wanted (for human readability).

    Parameters
    ----------
    entity_file: str
        The input entity file.

    type_file: str
        The input type file.

    save_json: bool
        Indicates, if the dictionaries should also be saved as .json files or not.
    """
    #Read in the files correctly
    entity_def = pd.read_csv(entity_file, delimiter=",", quotechar='"', converters={
        "Parameter_Name": lambda x: x.strip("[]").split(", "),
        "Parameter_Type": lambda x: x.strip("[]").split(", "),
        "Calling_Parameters": lambda x: x.strip("[]").split(", "),
        "Calling_Param_Types": lambda x: x.strip("[]").split(", "),
        "Supertypes": lambda x: x.strip("[]").split(", "),
        "Rules_Name": lambda x: x.strip("[]").split(", "),
        "Rules_Description": lambda x: x.strip("[]").split(", "),
        "Called_from_x_as": lambda x: x.strip("[]").split(", "),
        "Called_element_from_x": lambda x: x.strip("[]").split(", ")})
    type_def = pd.read_csv(type_file, delimiter=",", quotechar='"', converters={
        "Definition_List": lambda x: x.strip("[]").split(", ")})
    entity_dict = {}
    type_dict = {}

    count = 0
    for i, row in entity_def.iterrows():
        entity = row["Method"]
        params = row["Parameter_Name"]
        param_types = row["Parameter_Type"]
        #parent = row["Parent"]
        #children = row["Children"]
        #sap = row["Same_As_Parent"]
        desc = row["Description"]
        ref = row["Reference_of_documentation"]
        #used_for = row["Used_For"]
        used_by = row["Used_By?"]
        #informal_propositions = row["Informal_Propositions"]
        formal_propositions = row["Rules_Name"]
        formal_propositions_desc = row["Rules_Description"]
        call_params = row["Calling_Parameters"]
        call_param_types = row["Calling_Param_Types"]
        supertypes = row["Supertypes"]
        called_as = row["Called_from_x_as"]
        called_corresponding_entity = row["Called_element_from_x"]

        parameter_list = []
        if params[0] == '':
            params = []
        inner_count = 0

        for j in param_types:
            param_dict = {}
            param_split = re.split(r'\s+', j)
            if param_split[0] != '':
                is_list = "no"
                list_min = -1
                list_max = -1
                if len(param_split) > 1 and "[" in param_split[1]:
                    list_val = re.split(r'\[|:|\]', param_split[1])
                    if len(list_val) > 5:
                        is_list = "double"
                        list1_min = list_val[1]
                        list1_max = list_val[2]
                        list2_min = list_val[4]
                        list2_max = list_val[5]
                    else:
                        is_list = "single"
                        list_min = list_val[1]
                        list_max = list_val[2]

                if is_list == "double":
                    if param_split[-1] == "FIX":
                        if param_split[-2].endswith('?'):
                            param_dict[param_split[0]] = {'parameter_position': inner_count,
                                'parameter_type': 'type', 'required': False, 'is_list': is_list,
                                'list1_min': list1_min, 'list1_max': list1_max,
                                'list2_min': list2_min, 'list2_max': list2_max}
                        else:
                            param_dict[param_split[0]] = {'parameter_position': inner_count,
                                'parameter_type': 'type', 'required': True, 'is_list': is_list,
                                'list1_min': list1_min, 'list1_max': list1_max,
                                'list2_min': list2_min, 'list2_max': list2_max}
                    else:
                        if param_split[-1].endswith('?'):
                            param_dict[param_split[0]] = {'parameter_position':inner_count,
                                'parameter_type': 'entity', 'required': False, 'is_list': is_list,
                                'list1_min': list1_min, 'list1_max': list1_max,
                                'list2_min': list2_min, 'list2_max': list2_max}
                        else:
                            param_dict[param_split[0]] = {'parameter_position': inner_count,
                                'parameter_type': 'entity', 'required': True, 'is_list': is_list,
                                'list1_min': list1_min, 'list1_max': list1_max,
                                'list2_min': list2_min, 'list2_max': list2_max}

                else:
                    if param_split[-1] == "FIX":
                        if param_split[-2].endswith('?'):
                            param_dict[param_split[0]] = {'parameter_position': inner_count,
                                'parameter_type': 'type', 'required': False, 'is_list': is_list,
                                'list_min': list_min, 'list_max': list_max}
                        else:
                            param_dict[param_split[0]] = {'parameter_position': inner_count,
                                'parameter_type': 'type', 'required': True, 'is_list': is_list,
                                'list_min': list_min, 'list_max': list_max}
                    else:
                        if param_split[-1].endswith('?'):
                            param_dict[param_split[0]] = {'parameter_position': inner_count,
                                'parameter_type': 'entity', 'required': False, 'is_list': is_list,
                                'list_min': list_min, 'list_max': list_max}
                        else:
                            param_dict[param_split[0]] = {'parameter_position': inner_count,
                                'parameter_type': 'entity', 'required': True, 'is_list': is_list,
                                'list_min': list_min, 'list_max': list_max}
                parameter_list.append(param_dict)
            inner_count += 1


        calling_parameter_list = []
        calling_inner_count = 0

        for j in call_param_types:
            calling_param_dict = {}
            calling_param_split = re.split(r'\s+', j)
            if calling_param_split[0] != '':
                is_list = False
                list_min = -1
                list_max = -1
                if len(calling_param_split) > 2 and "[" in calling_param_split[2]:
                    list_val = re.split(r'\[|:|\]', calling_param_split[2])
                    is_list = True
                    list_min = list_val[1]
                    list_max = list_val[2]

                if calling_param_split[-1].endswith('?'):
                    calling_param_dict[calling_param_split[0]] = {
                        'parameter_position': calling_inner_count,
                        'parameter_type': 'entity', 'required': False, 'is_list': is_list,
                        'list_min': list_min, 'list_max': list_max,
                        'corresponding_entity': re.sub("@", "", calling_param_split[1])}
                else:
                    calling_param_dict[calling_param_split[0]] = {
                        'parameter_position': calling_inner_count,
                        'parameter_type': 'entity', 'required': True, 'is_list': is_list,
                        'list_min': list_min, 'list_max': list_max,
                        'corresponding_entity': re.sub("@", "", calling_param_split[1])}

                calling_parameter_list.append(calling_param_dict)
            calling_inner_count += 1


        called_ce_list = []
        for j in called_corresponding_entity:
            called_ce = re.split(r'\s+', j)[0]
            called_ce_list.append(called_ce)

        entity_dict[entity] = {'parameter_name': params, 'parameters': parameter_list,
            'supertypes': supertypes, 'description': desc, 'reference': ref, 'users': used_by,
            'rules_name': formal_propositions, 'rules_description': formal_propositions_desc,
            'calling_parameter_name': call_params, 'calling_parameters': calling_parameter_list,
            'called_as': called_as, 'called_corresponding_entity': called_ce_list}
        count += 1

    save_obj(entity_dict, "entities")

    count = 0
    for i, row in type_def.iterrows():
        type_name = row["Type"]
        type_type = row["Definition_Type"]
        def_list = row["Definition_List"]
        desc = row["Description"]
        ref = row["Reference_of_documentation"]
        formal_propositions = row["Formal_Propositions"]

        type_dict[type_name] = {'type_definition': type_type, 'definition_list': def_list,
        'description': desc, 'reference': ref}
        count += 1

    save_obj(type_dict, "types")

    #Save the files in .json format, if wanted.
    if save_json:
        a_file = open('dict_entity_output.json','w')
        json.dump(entity_dict, a_file, indent=4)
        a_file.close()

        b_file = open('dict_type_output.json','w')
        json.dump(type_dict, b_file, indent=4)
        b_file.close()
