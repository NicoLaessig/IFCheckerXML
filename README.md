# IFCheckerXML

With the IFCheckerXML .ifcxml files can be validated against general rules, as well as formal propositions, according to the IFC documentation.
The corresponding warnings and/or errors (if found) will be written as a .csv file containing multiple information about the specific error/warning.
The rules/formal propositions checked can be easily adapted, as explained below.

## 1. Source Files Information

The following corresponds to the files within the '/src/ifcxml-checker' folders.

- 'ifc_documentation_files/':
  - Entity_IFC4_ADD2_TC1.csv: Contains information about the whole entities of the current ISO standard (IFC4 ADD2 TC1; ISO 16739-1:2018) within the IFC documentation. Not all information is currently used/needed.
  - Type_IFC4_ADD2_TC1.csv: Contains information about the whole types of the current ISO standard (IFC4 ADD2 TC1; ISO 16739-1:2018) within the IFC documentation. Not all information is currently used/needed.
- ifchecker_main.py: Main file that will be executed
  - Requires two arguments:
    1. -i/--input: Specifies the input .ifcxml file
    2. -o/--output: Specifies the output .csv file name, if errors and/or warnings are found
- 'ifcheck/': Rest of the code files (more information can be found within the specific files)
  - '__init__.py': Init file
  - 'basic.py': Contains some basic functions needed, like saving or loading pickle files.
  - 'create_dictionary.py': Converts the 'Entity_IFC4_ADD2_TC1.csv' and 'Type_IFC4_ADD2_TC1.csv' into the needed dictionary structure. This only has to be run in case if the .csv files changes. Hence, it is not used within the main-file of the project that can be run.
  - 'formal_propositions.py': Contains all formal propositions and additionally needed functions to validate these.
  - 'validator.py': Main validation file. It iterates the input file and performs several needed checks. Also calls the needed corresponding methods of the formal_propositions file.
- 'obj/': Contains necessary entities and types information through a dictionary structure, saved as pickle files (created through the create_dictionary.py file).


## 2. What exactly is checked?

- Uniqueness of all IDs
- If referenced entities exist and if they have the same matching type
- If required attributes or entities are missing, also includes having an empty string for attributes as dummy values
- Occurrence violations of entities and types
- If attribute values are valid corresponding to their type
- Formal propositions


## 3. How to add/remove rules?

- To add a custom rule: 
  - 1. Add a function named after the rule to the 'formal_propositions_ifcxml.py' file with the structure "def {rule_name}(self, entity, ifcname, called_entity=None)
  - 2. Add {rule_name} to the "Rules_Name" column of the corresponding entity entry in 'Entity_IFC4_ADD2_TC1.csv'
  - 3. Call the 'create_dict' method with the following parameters: (1) Specified {entity}.csv and (2) {type}.csv files & (3) Boolean value if the created dictionaries should also be saved as .json files.
- To remove a rule:
  - 1. Remove the {rule_name} in the "Rules_Name" column of the corresponding entity entry in 'Entity_IFC4_ADD2_TC1.csv'
  - 2. Call the 'create_dict' method with the following parameters: (1) Specified {entity}.csv and (2) {type}.csv files & (3) Boolean value if the created dictionaries should also be saved as .json files.
- All rules defined in a supertype of an entity are automatically applied as well


## 4. Other Files Information

- 'tests/': 
  - Example .ifcxml files, with some of them being slightly adapted with added errors. Source of the original files can be found on the official IFC Documentation page: https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/annex/annex-e/
  - Corresponding results are saved in 'test/results/'. If no corresponding result file exists, then no error has been found.
- requirements.txt: Contains all python modules needed
