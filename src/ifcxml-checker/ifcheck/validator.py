"""
This python file validates the correctness of .ifc files and returns the list of
errors found (if any) via a .csv file.
For the validation check the newest ISO publicated IFC version is used: IFC4 ADD2 TC1.
"""
import re
from urllib.parse import urlparse
from datetime import datetime
from .basic import IntConv, FloatConv, BoolConv
from .formal_propositions import Rules


class Validator:
    """
    This class contains all rules and formal propositions defined in the IFC Documentation.
    Other rules, like if the correct type is applied, are not defined in this class.

    Parameters
    ----------
    tree: ElementTree
        It's the element tree of the .ifcxml structure.

    entities: dictionary
        Dictionary that contains all IFC Entities and related informations.

    types: dictionary
        Dictionary that contains all IFC Types and related informations.

    type_namespace: str
        This is the namespace used in type attributes.
    """
    def __init__(self, tree, entities, types, validation_output, type_namespace):
        self.tree = tree
        self.entities = entities
        self.types = types
        self.validation_df = validation_output
        self.type = type_namespace
        global R
        R = Rules(tree, entities, type_namespace)


    def return_result(self):
        """Returns the validation output file"""
        return self.validation_df


    def print_result(self, outputfile):
        """If errors have been found, the file will be saved as {outputfile}.csv
        Input: Name (& location) of the outputfile.
        Output: If errors/warnings are found, they are saved. Also it is printed if any
            error/warning is fouund."""
        if len(self.validation_df) > 0:
            print("Errors have been found in the .ifcxml file and have been saved to: "\
                + str(outputfile))
            self.validation_df.to_csv(outputfile, index=False)
        else:
            print("File validated successfully. No errors have been detected.")


    def add_to_csv(self, rowcount, line, index, error_type, error_message, rule_name, entity_type,\
        attribute_type, link, document_reference):
        """Adds a row to the validation dataframe. This is called when an error/warning has
        been found.
        Input: Several parameters about where the error is, what the error is and where it can be
            found in the official IFC documentation.
        Output: Number of dimensions of the given ifctype."""
        self.validation_df.at[rowcount, "line"] = line
        self.validation_df.at[rowcount, "id"] = index
        self.validation_df.at[rowcount, "error_type"] = error_type
        self.validation_df.at[rowcount, "error_message"] = error_message
        self.validation_df.at[rowcount, "rule_name"] = rule_name
        self.validation_df.at[rowcount, "entity_type"] = entity_type
        self.validation_df.at[rowcount, "attribute_type"] = attribute_type
        self.validation_df.at[rowcount, "link"] = link
        self.validation_df.at[rowcount, "document_reference"] = document_reference


    def dict_chapter(self, reference):
        """Returns the name of the ifc documentation chapter for a given reference, which is
        used in the documentation link.
        Input: Reference number of the ifc documentation.
        Output: The name of the ifc documentation chapter for the reference."""
        if reference.startswith("5."):
            if reference.startswith("5.1."):
                return "ifckernel"
            elif reference.startswith("5.2."):
                return "ifccontrolextension"
            elif reference.startswith("5.3."):
                return "ifcprocessextension"
            elif reference.startswith("5.4."):
                return "ifcproductextension"
        if reference.startswith("6."):
            if reference.startswith("6.1."):
                return "ifcsharedbldgelements"
            elif reference.startswith("6.2."):
                return "ifcsharedbldgserviceelements"
            elif reference.startswith("6.3."):
                return "ifcsharedcomponentelements"
            elif reference.startswith("6.4."):
                return "ifcsharedfacilitieselements"
            elif reference.startswith("6.5."):
                return "ifcsharedmgmtelements"
        if reference.startswith("7."):
            if reference.startswith("7.1."):
                return "ifcarchitecturedomain"
            elif reference.startswith("7.2."):
                return "ifcbuildingcontrolsdomain"
            elif reference.startswith("7.3."):
                return "ifcconstructionmgmtdomain"
            elif reference.startswith("7.4."):
                return "ifcelectricaldomain"
            elif reference.startswith("7.5."):
                return "ifchvacdomain"
            elif reference.startswith("7.6."):
                return "ifcplumbingfireprotectiondomain"
            elif reference.startswith("7.7."):
                return "ifcstructuralanalysisdomain"
            elif reference.startswith("7.8."):
                return "ifcstructuralelementsdomain"
        if reference.startswith("8."):
            if reference.startswith("8.1."):
                return "ifcactorresource"
            elif reference.startswith("8.2."):
                return "ifcapprovalresource"
            elif reference.startswith("8.3."):
                return "ifcconstraintresource"
            elif reference.startswith("8.4."):
                return "ifccostresource"
            elif reference.startswith("8.5."):
                return "ifcdatetimeresource"
            elif reference.startswith("8.6."):
                return "ifcexternalreferenceresource"
            elif reference.startswith("8.7."):
                return "ifcgeometricconstraintresource"
            elif reference.startswith("8.8."):
                return "ifcgeometricmodelresource"
            elif reference.startswith("8.9."):
                return "ifcgeometryresource"
            elif reference.startswith("8.10."):
                return "ifcmaterialresource"
            elif reference.startswith("8.11."):
                return "ifcmeasureresource"
            elif reference.startswith("8.12."):
                return "ifcpresentationappearanceresource"
            elif reference.startswith("8.13."):
                return "ifcpresentationdefinitionresource"
            elif reference.startswith("8.14."):
                return "ifcpresentationorganizationresource"
            elif reference.startswith("8.15."):
                return "ifcprofileresource"
            elif reference.startswith("8.16."):
                return "ifcpropertyresource"
            elif reference.startswith("8.17."):
                return "ifcquantityresource"
            elif reference.startswith("8.18."):
                return "ifcrepresentationresource"
            elif reference.startswith("8.19."):
                return "ifcstructuralloadresource"
            elif reference.startswith("8.20."):
                return "ifctopologyresource"
            elif reference.startswith("8.21."):
                return "ifcutilityresource"


    def unique_ids(self):
        """Checks if all IDs are unique, and if not return the non-unique ones.
        Input: No additional input needed, since it takes the tree of the class object.
        Output: Adds an error in the validation output file for each duplicate ID found."""
        all_ids = []
        double_ids = []

        #Add all IDs to a list, then sort the list and check if two IDs next to each other
        #are equal.
        for elem in self.tree.findall(".//*[@id]"):
            uid = elem.attrib["id"]
            all_ids.append(uid)
        all_ids.sort()
        for i in range(len(all_ids)):
            if all_ids[i] == all_ids[i-1]:
                double_ids.append(all_ids[i])

        if double_ids == []:
            #print("No duplicates detected")
            #return True
            pass

        else:
            double_ids = list(set(double_ids))
            double_id_lines = []
            for i in range(len(double_ids)):
                line_list = []
                double_id_lines.append(line_list)

            for elem in self.tree.findall(".//*[@id]"):
                if elem.attrib["id"] in double_ids:
                    id_index = double_ids.index(elem.attrib["id"])
                    double_id_lines[id_index].append(elem.sourceline)

            for i in range(len(double_ids)):
                line = double_id_lines[i]
                index = double_ids[i]
                error_type = "ID"
                error_message = "Multiple elements are using the same ID."
                self.add_to_csv(len(self.validation_df), line, index, error_type, error_message,
                    "", "", "", "", "")


    def typechecker_sequence(self, value, typename):
        """Checks the correctness of value for special sequential types.
        Input: A value & a given sequential type.
        Output: Returns True if the value is correct, else return an error message."""
        correctness = True
        #First split the values
        if " " in str(value):
            values = re.split(r'\s+', str(value))
        else:
            values = []
            values.append(value)
        #Following sequence possibilities
        if typename == "IfcArcIndex":
            if len(values) != 3:
                correctness = False
            else:
                for val in values:
                    val = IntConv(val)
                    if not isinstance(val, int):
                        correctness = False
                    elif val < 0:
                        correctness = False
        elif typename == "IfcLineIndex":
            if len(values) < 2:
                correctness = False
            else:
                for val in values:
                    val = IntConv(val)
                    if not isinstance(val, int):
                        correctness = False
                    elif val < 0:
                        correctness = False
        elif typename == "IfcPropertySetDefinitionSet":
            #Set of multiple IfcPropertySetDefinitions [1:?]
            pass
        elif typename == "IfcComplexNumber":
            values[0] = FloatConv(values[0])
            if len(values) == 1:
                if not isinstance(values[0], float):
                    correctness = False
            elif len(values) == 2:
                values[1] = FloatConv(values[1])
                if not isinstance(values[0], float):
                    correctness = False
                if not isinstance(values[1], float):
                    correctness = False
            else:
                #Illegal list size
                correctness = False
        elif typename == "IfcCompoundPlaneAngleMeasure":
            if len(values) == 3 or len(values) == 4:
                #If first measure is latitude or longitude, it has to be restricted
                values[0] = IntConv(values[0])
                values[1] = IntConv(values[1])
                values[2] = IntConv(values[2])
                if not isinstance(values[0], int):
                    correctness = False
                if not isinstance(values[1], int) or values[1] <= -60 or values[1] >= 60:
                    correctness = False
                if not isinstance(values[2], int) or values[2] <= -60 or values[2] >= 60:
                    correctness = False
                if len(values) == 4:
                    values[3] = IntConv(values[3])
                    if (
                        not isinstance(values[3], int)
                        or values[3] <= -1000000
                        or values[3] >= 1000000
                    ):
                        correctness = False
            else:
                #Illegal list size
                correctness = False
            positiveTrue = True
            negativeTrue = True
            for val in values:
                if val < 0:
                    positiveTrue = False
                elif val > 0:
                    negativeTrue = False
            if not positiveTrue and not negativeTrue:
                correctness = "Not all values have the same sign"
        else:
            correctness = "The typename is not in dictionary"

        return correctness


    def typechecker_type(self, value, typename):
        """Checks the correctness of value for common types.
        Input: A value & a given type.
        Output: Returns True if the value is correct, else return an error message."""
        correctness = True
        if typename == "IfcBinary":
            for i in range(len(str(value))):
                if str(value)[i] != "0" and str(value)[i] != "1":
                    correctness = False
                    break
        elif typename == "IfcBoolean":
            value = BoolConv(value)
            if not isinstance(value, bool):
                correctness = False
        elif typename == "IfcGloballyUniqueId":
            #There is an extra function for the ID checks
            if not isinstance(value, str) or len(value) > 22:
                correctness = False
        elif typename == "IfcIdentifier":
            if not isinstance(value, str) or len(value) > 255:
                correctness = False
        elif typename == "IfcInteger":
            value = IntConv(value)
            if not isinstance(value, int):
                correctness = False
        elif typename == "IfcLabel":
            if not isinstance(value, str) or len(value) > 255:
                correctness = False
        elif typename == "IfcLogical":
            select_list = ["TRUE", "FALSE", "UNKNOWN"]
            if str(value).lower() not in (str(item).lower() for item in select_list):
                correctness = False
        elif typename == "IfcNumericMeasure":
            #IfcNumericMeasure vs IfcReal?
            value = IntConv(value)
            value = FloatConv(value)
            if not isinstance(value, float) and not isinstance(value, int):
                correctness = False
        elif typename == "IfcParameterValue":
            value = FloatConv(value)
            if not isinstance(value, float):
                correctness = False
        elif typename == "IfcPositiveInteger":
            value = IntConv(value)
            if not isinstance(value, int) or int(value) <= 0:
                correctness = False
        elif typename == "IfcReal":
            value = FloatConv(value)
            if not isinstance(value, float):
                correctness = False
        elif typename == "IfcText":
            if not isinstance(value, str):
                correctness = False
        else:
            correctness = "The typename is not in dictionary"

        return correctness


    def typechecker_other(self, value, typename):
        """Checks the correctness of value for other types.
        Input: A value and a given type.
        Output: Returns True if the value is correct, else return an error message."""
        correctness = True
        if typename == "IfcDate":
            try:
                datetime.strptime(value, '%Y-%m-%d')
            except Exception:
                correctness = False
        elif typename == "IfcDateTime":
            try:
                datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
            except Exception:
                correctness = False
        elif typename == "IfcDuration":
            m = re.match(r'^P(?!$)(\d+Y)?(\d+M)?(\d+D)?(T(?=\d)(\d+H)?(\d+M)?(\d+S)?)?$', value)
            if m is None:
                correctness = False
        elif typename == "IfcTime":
            try:
                datetime.strptime(value, '%H:%M:%S')
            except Exception:
                correctness = False
        elif typename == "IfcTimeStamp":
            value = IntConv(value)
            if not isinstance(value, int):
                correctness = False
        elif typename == "IfcURIReference":
            #Might require some more testing
            try:
                urlparse(value)
            except Exception:
                correctness = False
        elif typename == "IfcPresentableText":
            #Text string in ISO 10303-21, does it have to be changed?
            if not isinstance(value, str):
                correctness = False
        else:
            correctness = "The typename is not in dictionary"

        return correctness


    def typechecker(self, value, typename, is_list):
        """Checks if the attribute value (or list of values) conforms to the given type.
        Input: A value, the given type and if the value is a list or not.
        Output: Returns True if the value (or list of values) is correct, else return an
            error message."""
        correctness = True
        type_type = self.types[typename]["type_definition"]
        if value is None:
            value = ""
        #REPRESENTATION SEQUENCE TYPE
        #If it is a sequence type, call the sequence function
        if type_type == "Representation/Sequence":
            current_val_correctness = self.typechecker_sequence(value, typename)
            if not current_val_correctness:
                correctness = current_val_correctness
        else:
            #If the input data is a list of values, split them. Check each value on its own.
            if is_list != "no" and " " in str(value):
                values = re.split(r'\s+', str(value))
            else:
                values = []
                values.append(value)
            correctness = True
            for i, val in enumerate(values):
                #TYPE ENUMERATION
                if type_type == "Enumeration":
                    if (str(val).lower() not in
                        (str(item).lower() for item in self.types[typename]["definition_list"])):
                        correctness = False
                #MEASURE TYPE
                elif type_type == "Measure":
                    if self.types[typename]["definition_list"][-1] == "REAL":
                        values[i] = FloatConv(values[i])
                        if not isinstance(values[i], float):
                            correctness = False
                    elif self.types[typename]["definition_list"][-1] == "STRING":
                        if not isinstance(values[i], str):
                            correctness = False
                    elif self.types[typename]["definition_list"][-1] == "NUMBER":
                        values[i] = IntConv(values[i])
                        values[i] = FloatConv(values[i])
                        if not isinstance(values[i], float) and not isinstance(values[i], int):
                            correctness = False
                    else:
                        correctness = "Measure type has not been found"
                #MINMAX AND EXCLUSIVE TYPE
                elif type_type == "Representation/MinMax":
                    values[i] = FloatConv(values[i])
                    if not isinstance(values[i], float):
                        correctness = False
                    else:
                        min_value = self.types[typename]["definition_list"][0]
                        max_value = self.types[typename]["definition_list"][-1]
                        if max_value == "...":
                            if float(min_value) > values[i]:
                                correctness = False
                        else:
                            if float(min_value) > values[i] or values[i] > float(max_value):
                                correctness = False
                elif type_type == "Representation/ExclusiveMinMax":
                    values[i] = FloatConv(values[i])
                    if not isinstance(values[i], float):
                        correctness = False
                    else:
                        min_value = self.types[typename]["definition_list"][0]
                        max_value = self.types[typename]["definition_list"][-1]
                        if max_value == "...":
                            if float(min_value) >= values[i]:
                                correctness = False
                        else:
                            if float(min_value) >= values[i] or values[i] > float(max_value):
                                correctness = False
                #REPRESENTATION CHOICE TYPE; check if the value is within the given list
                elif type_type == "Representation/Choice":
                    if (str(values[i]).lower() not in
                        (str(item).lower() for item in self.types[typename]["definition_list"])):
                        correctness = False
                #REPRESENTATION COMMON TYPE (like Integer, Identifier, etc.)
                elif type_type == "Representation/Type":
                    current_val_correctness = self.typechecker_type(values[i], typename)
                    if not current_val_correctness:
                        correctness = current_val_correctness
                #REPRESENTATION OTHER TYPE
                elif type_type == "Representation/Other":
                    current_val_correctness = self.typechecker_other(values[i], typename)
                    if not current_val_correctness:
                        correctness = current_val_correctness
                #TYPE SELECT
                #Select types typically have their own XML element instead of attribute.
                elif type_type == "Select":
                    correctness = "type_type is select?"
                #UNKNOWN TYPE
                else:
                    correctness = "Unknown file_type: " + str(typename) + ", "\
                        + str(type_type) + ", " + str(values[i])

                if not correctness:
                    return correctness

        return correctness


    def reference_checker(self, entity):
        """Checks if a referenced object type is the same as the object type of the one
        referencing it.
        Input: An entity.
        Output: If the referenced object is found, and if so, if its type is equal."""
        found_ref = False
        is_equal = None
        ref = entity.attrib["ref"]
        #In the .ifcxml version the tree has to be iterated to find the corresponding referenced
        #object via id.
        for elem in self.tree.findall(".//*[@id]"):
            uid = elem.attrib["id"]
            if ref == uid:
                found_ref = True
                if self.type in elem.attrib and self.type in entity.attrib:
                    is_equal = bool(elem.attrib[self.type] == entity.attrib[self.type])
                elif self.type in elem.attrib:
                    is_equal = bool(elem.attrib[self.type] == entity.tag)
                elif self.type in entity.attrib:
                    is_equal = bool(elem.tag == entity.attrib[self.type])
                else:
                    is_equal = bool(elem.tag == entity.tag)
                break
        return found_ref, is_equal


    def check_children(self, current_entity, ifcname, children_list, children_type_list,
        calling_list, calling_type_list, ifc_list, called_entity=None):
        """Checks if the rules and formal propositions are valid for each XML element/IFC entity.
        Input: Current entity, its ifc type and children and additional information.
        Output: Adds an error in the validation output file for each error or warning found.
            The file is iteratively checked."""

        docpage = "https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/schema/"
        #Check if current entity is a reference & if so, throw errors if the referenced id cannot
        #be found or if the referenced entity has a different type.
        if "ref" in current_entity.attrib:
            found_ref, is_equal = self.reference_checker(current_entity)
            if not found_ref:
                error_type = "Reference"
                error_message = "Referenced id can not be found. ID: "\
                    + str(current_entity.attrib["ref"])
                ref_id = "referenced id: " + str(current_entity.attrib["ref"])
                self.add_to_csv(len(self.validation_df), current_entity.sourceline, ref_id, error_type,
                    error_message, "", "", "", "", "")
            elif not is_equal:
                error_type = "Reference"
                error_message = "The reference type is not matching. Referenced ID: "\
                    + str(current_entity.attrib["ref"])
                ref_id = "referenced id: " + str(current_entity.attrib["ref"])
                self.add_to_csv(len(self.validation_df), current_entity.sourceline, ref_id, error_type,
                    error_message, "", "", "", "", "")

        #Skip the test if the current child has "-wrapper" assigned to its tag. This is done by
        #converting selected attributes (through choice lists) into the .xml format.
        #In addition to their attribute type, the string "-wrapper" will be added to at the end
        #of the type name.
        #If the values assigned to that are correct/allowed is checked in another part of the code
        #(already at the stage of the parent node).
        elif ifcname.endswith("-wrapper"):
            pass

        #If the current element is neither a reference to another one nor it is an attribute
        #element, then perform all other tests/checks on the current entity. This includes
        #validation checks of normal rules, as well as formal proposition validation.
        else:
            current_doc_reference = self.entities[ifcname]["reference"]
            dict_chapter = self.dict_chapter(current_doc_reference)
            link = docpage + str(dict_chapter) + "/lexical/" + ifcname.lower() + ".htm"
            current_entity_children = []
            #Check for each child element, if it is in the allowed child element list.
            for child in current_entity:
                if (
                    child.tag not in self.entities[ifcname]["parameter_name"]
                    and child.tag not in self.entities[ifcname]["calling_parameter_name"]
                ):
                    error_type = "Unknown child"
                    error_message = "The element " + str(child.tag)\
                        + " is not a valid entity/child for the current entity type "\
                        + str(ifcname) + " according to the documentation."
                    self.add_to_csv(len(self.validation_df), current_entity.sourceline,
                        current_entity.attrib["id"], error_type, error_message, "", ifcname, "",
                        link, current_doc_reference)
                #If the child element is allowed, add it to the list of children of the current
                #entity.
                else:
                    current_entity_children.append(child.tag)
            #Check if no (direct) child occurs multiple times.
            if len(current_entity_children) != len(set(current_entity_children)):
                error_type = "List size violation"
                error_message = "One of the children of the current entity occurs too often."
                self.add_to_csv(len(self.validation_df), current_entity.sourceline,
                    current_entity.attrib["id"], error_type, error_message, "", ifcname, "", link,
                    current_doc_reference)

            #Check if all attributes are in the allowed attributes list.
            for attr in current_entity.attrib:
                standard_attributes_list = [self.type, "ref", "id",
                    "{http://www.w3.org/2001/XMLSchema-instance}nil", "pos"]
                if (
                    attr not in self.entities[ifcname]["parameter_name"]
                    and attr not in standard_attributes_list
                ):
                    if "id" in current_entity.attrib:
                        index = current_entity.attrib["id"]
                    else:
                        index = current_entity.attrib["ref"]
                    error_type = "Unknown attribute"
                    error_message = "The attribute " + str(attr)\
                        + " is unknown according to the documentation."
                    self.add_to_csv(len(self.validation_df), current_entity.sourceline, index,
                        error_type, error_message, "", ifcname, "", link, current_doc_reference)

            #######################################################################################
            #### 1. Validate occurrence of all attributes. ########################################
            #### 2. Validate the value of the attribute types. ####################################
            #### 3. Validate if required children entities exist. #################################
            #######################################################################################

            #Check now if all attributes and child elements/entities are valid.
            for i, param in enumerate(self.entities[ifcname]["parameters"]):
                current_param = self.entities[ifcname]["parameter_name"][i]
                current_param_ifcname = list(param.keys())[0]
                current_param_type = param[current_param_ifcname]["parameter_type"]
                current_param_req = param[current_param_ifcname]["required"]
                is_list = param[current_param_ifcname]["is_list"]
                if is_list == "single":
                    list_min = param[current_param_ifcname]["list_min"]
                    list_max = param[current_param_ifcname]["list_max"]
                elif is_list == "double":
                    list1_min = param[current_param_ifcname]["list1_min"]
                    list1_max = param[current_param_ifcname]["list1_max"]
                    list2_min = param[current_param_ifcname]["list2_min"]
                    list2_max = param[current_param_ifcname]["list2_max"]
                #If it is no list, it can just be one item maximum. If the attribute/entity
                #is not required, then the minimum can be 0.
                else:
                    list_min = 1 if current_param_req else 0
                    list_max = 1

                #Check if current parameter is an attribute/type. If yes, check if required
                #attributes are given and if the types of the given attributes are correct.
                if current_param_type == "type":
                    error_msg = None
                    error_type = "Type"
                    position_of_param = self.entities[ifcname]["parameter_name"].index(current_param)
                    typename = list(self.entities[ifcname]["parameters"][position_of_param].keys())[0]
                    current_attrib_type = self.types[typename]["type_definition"]
                    #If the current attribute is not in the attributes list and it is of attribute
                    #type "Select", then check if it is within the list of child elements.
                    if (
                        current_param not in current_entity.attrib
                        and current_attrib_type == "Select"
                    ):
                        param_found = current_entity.find(current_param)
                        #If current attribute of type "select" doesn't exist as a child element,
                        #and it is required, then throw a warning/error message.
                        if param_found is None and current_param_req:
                            error_type = "Missing Information"
                            error_msg = "Required select child " + str(current_param)\
                                + " does not exist."
                        #If the child element can be found, check if the type used is valid.
                        elif param_found is not None:
                            select_list = self.types[typename]["definition_list"]
                            #If the child attribute should only occur once, put it in a list as the
                            #only element. Then iterate the list and check for each child if the
                            #attribute type is allowed and its correspondent value is valid.
                            if is_list == "no":
                                param_found = [param_found[0]]
                            for curr_param_elem in param_found:
                                curr_param = curr_param_elem.tag
                                child_type = re.sub("-wrapper", "", curr_param_elem.tag)
                                #If the select attribute type let's select between entities, the
                                #element tag does not include "-wrapper". Then it just has to be
                                #checked if the element is among the selection list.
                                if (
                                    not curr_param.endswith("-wrapper")
                                    and curr_param not in select_list
                                    and len(set(self.entities[curr_param]["supertypes"])
                                            .intersection(set(select_list))) == 0
                                ):
                                    error_msg = "Chosen entity " + str(current_param)\
                                        + " is not reflected in the select list."

                                elif (
                                    curr_param.endswith("-wrapper")
                                    and child_type not in select_list
                                ):
                                    error_msg = "Chosen type " + str(child_type)\
                                        + " is not reflected in the select list."

                                #If the child is an attribute that is within the select list, check
                                #its value for correctness.
                                elif curr_param.endswith("-wrapper"):
                                    value = curr_param_elem.text
                                    correctness = self.typechecker(value, child_type, False)
                                    #A string message only takes place in case of a special error,
                                    #e.g. when a type is unknown, so it cannot be checked.
                                    if isinstance(correctness, str):
                                        error_msg = correctness + " (" + str(current_param) + ")"
                                    elif not correctness:
                                        error_msg = "The attribute " + str(current_param)\
                                            + " has a prohibited value. The value '"\
                                            + str(value) + "' does not fit the corresponding type "\
                                            + str(child_type) + "."

                            #Now check if the amount of times an attribute occured is correct.
                            if is_list == "double":
                                list_min = int(list1_min)*int(list2_min)
                                if list1_max == "?" or list2_max == "?":
                                    list_max = "?"
                                else:
                                    list_max = int(list1_max)*int(list2_max)

                            list_viol = False
                            if list_max != "?" and len(param_found) > int(list_max):
                                list_viol = True
                                list_viol_msg = "The select attribute " + str(current_param)\
                                    + " has too many children."
                            elif len(param_found) < int(list_min):
                                list_viol = True
                                list_viol_msg = "The select attribute " + str(current_param)\
                                    + " has too few children."
                            elif (
                                is_list == "double"
                                and list2_max != "?"
                                and int(list2_min) == int(list2_max)
                                and len(param_found) % int(list2_min) != 0
                            ):
                                list_viol = True
                                list_viol_msg = "The number of child elements of the select attribute "\
                                + str(current_param) + " is not correct (double list error)."

                            #If a list violation occurs, print an error message
                            if list_viol:
                                error_type = "List size violation"
                                error_message = list_viol_msg
                                attribute_type = current_param
                                self.add_to_csv(len(self.validation_df), current_entity.sourceline,
                                    current_entity.attrib["id"], error_type, error_message, "",
                                    ifcname, attribute_type, link, current_doc_reference)

                            for child in current_entity:
                                if child.tag == current_param and "ref" in child[0].attrib:
                                    found_ref, is_equal = self.reference_checker(child[0])
                                    if not found_ref:
                                        error_msg = "Referenced id can not be found."
                                        error_type = "Reference"
                                    elif not is_equal:
                                        error_msg = "The reference type is not matching."
                                        error_type = "Reference"

                    #Special case for attributes with double lists/sets values. In this case the
                    #attribute values are within child elements as well. Checks are similar to
                    #the select-type ones.
                    elif (current_param not in current_entity.attrib
                        and is_list == "double"
                    ):
                        double_param = current_entity.find(current_param)
                        if double_param is None:
                            if current_param_req:
                                error_type = "Missing Information"
                                error_msg = "Required attribute " + str(current_param)\
                                    + " does not exist."
                        elif len(double_param) < int(list1_min):
                            error_type = "List size violation"
                            error_msg = "The attribute " + str(current_param)\
                                + " has too little values. (double list error)"
                        elif list1_max != "?" and len(double_param) > int(list1_max):
                            error_type = "List size violation"
                            error_msg = "The attribute " + str(current_param)\
                                + " has too many values. (double list error)"
                        else:
                            for j, dp in enumerate(double_param):
                                child_type = re.sub("-wrapper", "", dp.tag)
                                if (
                                    child_type != current_param_ifcname
                                    and current_param_ifcname
                                    not in self.entities[child_type]["supertypes"]
                                ):
                                    error_msg = "Chosen type " + str(child_type)\
                                        + " is not reflected in the select list."
                                else:
                                    value = dp.text
                                    correctness = self.typechecker(value, child_type, False)
                                    if isinstance(correctness, str):
                                        error_msg = correctness + " (" + str(current_param) + ")"
                                    elif not correctness:
                                        error_msg = "The attribute " + str(current_param)\
                                            + " has a prohibited value."

                    #For all other required attributes, check if they exist.
                    elif current_param not in current_entity.attrib:
                        if current_param_req:
                            error_type = "Missing Information"
                            error_msg = "Required attribute " + str(current_param) + " does not exist."

                    #If the required attribute is within the list, but no value is given.
                    elif current_entity.attrib[current_param] == "":
                        if current_param_req:
                            error_type = "Missing Information"
                            error_msg = "Required attribute " + str(current_param) + " has no value."

                    #Check all other existing attributes for list violation and type violations.
                    else:
                        attr_value = current_entity.attrib[current_param]
                        list_viol = False
                        if is_list == "single":
                            if list_max != "?":
                                if len(re.split(r'\s+', str(attr_value))) > int(list_max):
                                    list_viol = True
                                    list_viol_msg = "The attribute " + str(current_param)\
                                        + " has too many values."
                            if len(re.split(r'\s+', str(attr_value))) < int(list_min):
                                list_viol = True
                                list_viol_msg = "The attribute " + str(current_param)\
                                    + " has too few values."
                        elif is_list == "double":
                            if (
                                list1_max != "?" and list2_max != "?"
                                and (len(re.split(r'\s+', str(attr_value)))
                                    > int(list1_max)*int(list2_max))
                            ):
                                list_viol = True
                                list_viol_msg = "The attribute " + str(current_param)\
                                    + " has too many values."
                            if len(re.split(r'\s+', str(attr_value))) < int(list1_min)*int(list2_min):
                                list_viol = True
                                list_viol_msg = "The attribute " + str(current_param)\
                                    + " has too little values."
                            elif (
                                list2_max != "?"
                                and int(list2_min) == int(list2_max)
                                and len(re.split(r'\s+', str(attr_value))) % int(list2_min) != 0
                            ):
                                list_viol = True
                                list_viol_msg = "The number of values in the attribute is not "\
                                    "correct (double list error)."
                        if list_viol:
                            error_type = "List size violation"
                            error_message = list_viol_msg
                            attribute_type = current_param
                            self.add_to_csv(len(self.validation_df), current_entity.sourceline,
                                current_entity.attrib["id"], error_type, error_message, "",
                                ifcname, attribute_type, link, current_doc_reference)

                        #Now check all existing attributes for their values
                        correctness = self.typechecker(attr_value, current_param_ifcname, is_list)
                        if isinstance(correctness, str):
                            error_msg = correctness + " (" + str(current_param) + ")"
                        elif not correctness:
                            error_msg = "The attribute " + str(current_param)\
                                + " has a prohibited value. Value (or list of values) "\
                                + str(attr_value) + " should be of type "\
                                + str(current_param_ifcname)

                    #If an attribute related error (apart from list violation) happened, add it to
                    #the output list. List violations are caught above differently, since they can
                    #co-appear with the other errors.
                    if error_msg is not None:
                        if error_type == "Type":
                            attribute_type = current_param_ifcname
                        else:
                            attribute_type = ""

                        self.add_to_csv(len(self.validation_df), current_entity.sourceline,
                            current_entity.attrib["id"], error_type, error_msg, "", ifcname,
                            attribute_type, link, current_doc_reference)


                #Check if required children elements/entities exist. If entity is called one,
                #then also check if the current checked parameter is the one being called.
                else:
                    if current_param_req and current_param not in current_entity_children:
                        if str(current_param) == str(called_entity):
                            continue

                        correct_called_entity = False
                        identifier = current_entity.attrib['id']
                        referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                        called_as = self.entities[ifcname]["called_as"]
                        if len(referenced) > 0:
                            for ref in referenced:
                                referenced_name = False
                                if ref.tag in called_as:
                                    referenced_name = ref.tag
                                elif ref.getparent().tag in called_as:
                                    referenced_name = ref.getparent().tag

                                if referenced_name:
                                    pos_called_param = called_as.index(referenced_name)
                                    called_from_as_entity = self.entities[ifcname]\
                                        ["called_corresponding_entity"][pos_called_param]
                                    if called_from_as_entity == current_param:
                                        correct_called_entity = True
                                        break

                        if not correct_called_entity:
                            error_type = "Missing Information"
                            error_message = "Required child " + str(current_param)\
                                + " does not exist."
                            self.add_to_csv(len(self.validation_df), current_entity.sourceline,
                                current_entity.attrib["id"], error_type, error_message, "",
                                ifcname, "", link, current_doc_reference)


            #######################################################################################
            ### 4. Check all formal propositions of the current entity type and its supertypes ####
            #######################################################################################

            #Automatically call all corresponding formal proposition methods defined.
            if self.entities[ifcname]["rules_name"][0] != "":
                for rule in self.entities[ifcname]["rules_name"]:
                    try:
                        call_function = rule
                        if called_entity is not None:
                            rule_result = getattr(R, rule)(current_entity, ifcname, called_entity)
                        else:
                            rule_result = getattr(R, rule)(current_entity, ifcname)
                        if rule_result is not None:
                            error_type = "Rule violation"
                            error_message = rule_result
                            self.add_to_csv(len(self.validation_df), current_entity.sourceline,
                                current_entity.attrib["id"], error_type, error_message, rule,
                                ifcname, "", link, current_doc_reference)
                    except Exception as e:
                        error_type = "Code Exception (rule checking)"
                        error_message = "Code Exception during rule checking. Probably an "\
                            "attribute or element is missing. Look at the other warnings/errors "\
                            "for possible causes. Error message: " + str(e)
                        self.add_to_csv(len(self.validation_df), current_entity.sourceline,
                            current_entity.attrib["id"], error_type, error_message, rule,
                            ifcname, "", link, current_doc_reference)

            if self.entities[ifcname]["supertypes"][0] != "":
                for i in range(len(self.entities[ifcname]["supertypes"])):
                    supertype_ifc = self.entities[ifcname]["supertypes"][i]
                    supertype_chapter = self.dict_chapter(self.entities[supertype_ifc]["reference"])
                    link = docpage + str(supertype_chapter) + "/lexical/" + supertype_ifc.lower() + ".htm"
                    if self.entities[supertype_ifc]["rules_name"][0] != "":
                        for rule in self.entities[supertype_ifc]["rules_name"]:
                            try:
                                if called_entity is not None:
                                    rule_result = getattr(R, rule)(current_entity, supertype_ifc, called_entity)
                                else:
                                    rule_result = getattr(R, rule)(current_entity, supertype_ifc)
                                if rule_result is not None:
                                    error_type = "Parent Rule violation"
                                    error_message = rule_result
                                    attribute_type = "SUPERTYPE: " + supertype_ifc
                                    self.add_to_csv(len(self.validation_df), current_entity.sourceline,
                                        current_entity.attrib["id"], error_type, error_message, rule,
                                        ifcname, attribute_type, link, current_doc_reference)
                            except Exception as e:
                                error_type = "Code Exception (rule checking)"
                                error_message = "Code Exception during rule checking. Probably "\
                                    "an attribute or element is missing. Look at the other "\
                                    "warnings/errors  for possible causes. Error message: "\
                                    + str(e)
                                attribute_type = "SUPERTYPE: " + supertype_ifc
                                self.add_to_csv(len(self.validation_df), current_entity.sourceline,
                                    current_entity.attrib["id"], error_type, error_message, rule,
                                    ifcname, attribute_type, link, current_doc_reference)

            #######################################################################################
            #### 5. Check all children entity elements for list violations ########################
            #### 6. Check all children entity elements for type violations ########################
            #### 7. Recursively call children elements ############################################
            #######################################################################################

            #Check the children elements and call them recursively correctly
            if len(current_entity_children) != 0:
                current_ifc = ifcname
                for child in current_entity:
                    if child.tag in current_entity_children:
                        sub_ifcname = "no"
                        ###########################################################################
                        ### Following validates normal children entity elements. ##################
                        ###########################################################################
                        if child.tag in self.entities[ifcname]["parameter_name"]:
                            position_of_param = self.entities[ifcname]["parameter_name"]\
                                .index(child.tag)
                            ifcname = list(self.entities[ifcname]["parameters"][position_of_param]\
                                .keys())[0]
                            is_list = self.entities[current_ifc]["parameters"][position_of_param]\
                                [ifcname]["is_list"]
                            current_type = self.entities[current_ifc]["parameters"][position_of_param]\
                                [ifcname]["parameter_type"]
                            if self.type in child.attrib:
                                sub_ifcname = child.attrib[self.type]
                            elif child.tag.startswith("Ifc"):
                                sub_ifcname = child.tag
                            if sub_ifcname != "no":
                                if sub_ifcname != ifcname:
                                    if ifcname in self.entities[sub_ifcname]["supertypes"]:
                                        ifcname = sub_ifcname
                                    else:
                                        error_type = "Entity"
                                        error_message = "Entity is using the wrong type."
                                        self.add_to_csv(len(self.validation_df), current_entity.sourceline,
                                            current_entity.attrib["id"], error_type, error_message,
                                            "", ifcname, "", link, current_doc_reference)

                            #Check for list violations
                            if is_list != "no":
                                list_viol = False
                                if is_list == "single":
                                    list_max = self.entities[current_ifc]["parameters"]\
                                        [position_of_param][ifcname]["list_max"]
                                    list_min = self.entities[current_ifc]["parameters"]\
                                        [position_of_param][ifcname]["list_min"]
                                    if list_max != "?":
                                        if len(child) > int(list_max):
                                            list_viol = True
                                            list_viol_msg = "The number of child elements is too big."
                                    if len(child) < int(list_min):
                                        list_viol = True
                                        list_viol_msg = "The number of child elements is too small."
                                elif is_list == "double":
                                    list1_max = self.entities[current_ifc]["parameters"]\
                                        [position_of_param][ifcname]["list1_max"]
                                    list2_max = self.entities[current_ifc]["parameters"]\
                                        [position_of_param][ifcname]["list2_max"]
                                    list1_min = self.entities[current_ifc]["parameters"]\
                                        [position_of_param][ifcname]["list1_min"]
                                    list2_min = self.entities[current_ifc]["parameters"]\
                                        [position_of_param][ifcname]["list2_min"]
                                    if list1_max != "?" and list2_max != "?":
                                        if len(child) > int(list1_max)*int(list2_max):
                                            list_viol = True
                                            list_viol_msg = "The number of child elements is too big."
                                    if len(child) < int(list1_min)*int(list2_min):
                                        list_viol = True
                                        list_viol_msg = "The number of child elements is too small."
                                    elif list2_max != "?":
                                        if int(list2_min) == int(list2_max):
                                            if len(child) % int(list2_min) != 0:
                                                list_viol = True
                                                list_viol_msg = "The number of child elements "\
                                                    "is not correct (double list error)."
                                if list_viol:
                                    error_type = "List size violation"
                                    error_message = list_viol_msg
                                    self.add_to_csv(len(self.validation_df), current_entity.sourceline,
                                        current_entity.attrib["id"], error_type, error_message,
                                        "", ifcname, "", link, current_doc_reference)

                                for chi in child:
                                    ifcname = chi.tag
                                    ifc_list.append(ifcname)
                                    #try:
                                    self.check_children(chi, chi.tag, children_list,
                                        children_type_list, calling_list, calling_type_list,
                                        ifc_list)
                                    #except Exception as e:
                                     #   error_type = "An unexpected Error occurred (1)"
                                      #  error_message = e
                                       # self.add_to_csv(len(self.validation_df), current_entity.sourceline,
                                        #    current_entity.attrib["id"], error_type, error_message,
                                         #   "", ifcname, "", "", "")
                                    if len(ifc_list) >= 1:
                                        del ifc_list[-1]
                                        if len(ifc_list) >= 1:
                                            ifcname = ifc_list[-1]

                            #Check if the child is a special (select) attribute type
                            elif current_type == "type":
                                ifcname = child[0].tag
                                ifc_list.append(ifcname)
                                try:
                                    self.check_children(child[0], child[0].tag, children_list,
                                        children_type_list, calling_list, calling_type_list,
                                        ifc_list)
                                except Exception as e:
                                    error_type = "An unexpected Error occurred (2)"
                                    error_message = e
                                    self.add_to_csv(len(self.validation_df), current_entity.sourceline,
                                        current_entity.attrib["id"], error_type, error_message,
                                        "", ifcname, "", "", "")
                                if len(ifc_list) >= 1:
                                    del ifc_list[-1]
                                    if len(ifc_list) >= 1:
                                        ifcname = ifc_list[-1]
                            else:
                                ifc_list.append(ifcname)
                                #try:
                                self.check_children(child, ifcname, children_list, children_type_list,
                                    calling_list, calling_type_list, ifc_list)
                                #except Exception as e:
                                    #error_type = "An unexpected Error occurred (3)"
                                    #error_message = e
                                    #self.add_to_csv(len(self.validation_df), current_entity.sourceline,
                                     #   current_entity.attrib["id"], error_type, error_message,
                                      #  "", ifcname, "", "", "")
                                if len(ifc_list) >= 1:
                                    del ifc_list[-1]
                                    if len(ifc_list) >= 1:
                                        ifcname = ifc_list[-1]

                        ###########################################################################
                        ### Following validates special calling parameter child elements. #########
                        ###########################################################################
                        elif child.tag in self.entities[ifcname]["calling_parameter_name"]:
                            position_of_param = self.entities[ifcname]["calling_parameter_name"]\
                                .index(child.tag)
                            ifcname2 = ifcname
                            ifcname = list(self.entities[ifcname]["calling_parameters"][position_of_param]\
                                .keys())[0]
                            is_list = self.entities[current_ifc]["calling_parameters"][position_of_param]\
                                [ifcname]["is_list"]


                            called_entity = self.entities[ifcname2]["calling_parameters"][position_of_param]\
                                [ifcname]["corresponding_entity"]

                            list_viol = False
                            list_max = self.entities[current_ifc]["calling_parameters"][position_of_param]\
                                [ifcname]["list_max"]
                            list_min = self.entities[current_ifc]["calling_parameters"][position_of_param]\
                                [ifcname]["list_min"]
                            if list_max == "1":
                                if "id" not in child.attrib and "ref" not in child.attrib:
                                    if len(child) > 1:
                                        list_viol = True
                                        list_viol_msg = "The number of child elements is too big."
                            elif list_max != "?":
                                if len(child) > int(list_max):
                                    list_viol = True
                                    list_viol_msg = "The number of child elements is too big."
                            if len(child) < int(list_min):
                                list_viol = True
                                list_viol_msg = "The number of child elements is too small."

                            if list_viol:
                                error_type = "List size violation"
                                error_message = list_viol_msg
                                self.add_to_csv(len(self.validation_df), child.sourceline,
                                    current_entity.attrib["id"], error_type, error_message,
                                    "", ifcname, "", link, current_doc_reference)

                            if list_max != "1":
                                for chi in child:
                                    ifcname = chi.tag
                                    ifc_list.append(ifcname)
                                    try:
                                        self.check_children(chi, ifcname, children_list, children_type_list,
                                            calling_list, calling_type_list, ifc_list, called_entity)
                                    except Exception as e:
                                        error_type = "An unexpected Error occurred (4)"
                                        error_message = e
                                        self.add_to_csv(len(self.validation_df), chi.sourceline,
                                            chi.attrib["id"], error_type, error_message, "",
                                            ifcname, "", "", "")
                                    if len(ifc_list) >= 1:
                                        del ifc_list[-1]
                                        if len(ifc_list) >= 1:
                                            ifcname = ifc_list[-1]
                            else:
                                ifc_list.append(ifcname)
                                try:
                                    self.check_children(child, ifcname, children_list, children_type_list,
                                        calling_list, calling_type_list, ifc_list, called_entity)
                                except Exception as e:
                                    error_type = "An unexpected Error occurred (5)"
                                    error_message = e
                                    self.add_to_csv(len(self.validation_df), child.sourceline,
                                        child.attrib["id"], error_type, error_message, "",
                                        ifcname, "", "", "")
                                if len(ifc_list) >= 1:
                                    del ifc_list[-1]
                                    if len(ifc_list) >= 1:
                                        ifcname = ifc_list[-1]
