"""
This python file includes all official IFC4 Formal Propositions and can be extended with
custom rules.
"""
import re
import math
from .basic import BoolConv


class Rules:
    """
    This class contains all rules and formal propositions defined in the IFC Documentation.
    Other rules, like if the correct type is applied, are not defined in this class.

    Parameters
    ----------
    tree: ElementTree
        It's the element tree of the .ifcxml structure.

    entities: dictionary
        Dictionary that contains all the entities and related informations.

    type_namespace: str
        This is the namespace used in type attributes.
    """
    def __init__(self, tree, entities, type_namespace):
        self.tree = tree
        self.entities = entities
        self.type = type_namespace

    ####################################################
    #Additional needed functions for the rules checking#
    ####################################################

    def ref_check(self, entity):
        """
        It returns the referenced entity of the given entity. Prior checks are required,
        if the current entity is a reference to another one.
        Input: Entity.
        Output: Referenced Entity.
        """
        ref = entity.attrib["ref"]
        entity_out = self.tree.find(f".//*[@id='{ref}']")
        return entity_out


    def attr_check(self, type1, type2):
        """
        Checks if an entity has a specific type or subtype of it.
        Input: An entity and a type.
        Output: Boolean value; True if current entity is of that type or subtype.
        """
        return bool(type1 == type2 or type2 in self.entities[type1]["supertypes"])


    def attr_list_check(self, type1, type_list):
        """
        Checks if an entity has a specific type of a list or subtype of it.
        Input: An entity and a type.
        Output: Boolean value; True if current entity is has one of the types of the list
            or is a subtype of one of them.
        """
        return bool(type1 in type_list
            or len(set(self.entities[type1]["supertypes"]).intersection(set(type_list))) != 0)


    def elements_equal(self, elem_1, elem_2):
        """
        Checks if two elements are equal.
        Input: Two elements.
        Output: Boolean value; True if both elements are equal, False otherwise.
        """
        if elem_1.tag != elem_2.tag:
            return False
        if elem_1.text != elem_2.text:
            return False
        if elem_1.tail != elem_2.tail:
            return False
        if elem_1.attrib != elem_2.attrib:
            return False
        if len(elem_1) != len(elem_2):
            return False
        return True


    def IfcDimensionSize(self, entity, ifctype):
        """
        Returns the dimension of an ifctype.
        Input: The entity and the ifctype of the entity.
        Output: Number of dimensions of the given ifctype.
        """
        if ifctype in (
            "IfcBSplineCurve",
            "IfcBSplineCurveWithKnots",
            "IfcRationalBSplineCurveWithKnots",
        ):
            bspline = entity.find("ControlPointsList")[0]
            if "ref" in bspline.attrib:
                bspline = self.ref_check(bspline)
            dim = len(re.split(r"\s+", str(bspline.attrib["Coordinates"])))
        elif ifctype in (
            "IfcCompositeCurve",
            "IfcCompositeCurveOnSurface",
            "IfcBoundaryCurve",
            "IfcOuterBoundaryCurve",
        ):
            composite = entity.find("Segments")[0]
            if "ref" in composite.attrib:
                composite = self.ref_check(composite)
            cc = composite.find("ParentCurve")
            if "ref" in cc.attrib:
                cc = self.ref_check(cc)
            ifccc = cc.attrib[self.type] if self.type in cc.attrib else cc.tag
            dim = self.IfcDimensionSize(cc, ifccc)
        elif ifctype in ("IfcConic", "IfcCircle", "IfcEllipse"):
            conic = entity.find("Position")[0]
            if "ref" in conic.attrib:
                conic = self.ref_check(conic)
            conic_type = conic.attrib[self.type] if self.type in conic.attrib else conic.tag
            if conic_type == "IfcAxis2Placement2D":
                dim = 2
            elif conic_type == "IfcAxis2Placement3D":
                dim = 3
        elif ifctype == "IfcIndexedPolyCurve":
            ipc = entity.find("Points")
            if "ref" in ipc.attrib:
                ipc = self.ref_check(ipc)
            ipc_type = ipc.attrib[self.type] if self.type in ipc.attrib else ipc.tag
            if ipc_type == "IfcCartesianPointList2D":
                dim = 2
            elif ipc_type == "IfcCartesianPointList3D":
                dim = 3
        elif ifctype == "IfcLine":
            line = entity.find("Pnt")
            if "ref" in line.attrib:
                line = self.ref_check(line)
            dim = len(re.split(r"\s+", str(line.attrib["Coordinates"])))
        elif ifctype == "IfcOffsetCurve2D":
            dim = 2
        elif ifctype == "IfcOffsetCurve3D":
            dim = 3
        elif ifctype == "IfcPcurve":
            dim = 3
        elif ifctype == "IfcPolyline":
            polyline = entity.find("Points")[0]
            if "ref" in polyline.attrib:
                polyline = self.ref_check(polyline)
            dim = len(re.split(r"\s+", str(polyline.attrib["Coordinates"])))
        elif ifctype == "IfcTrimmedCurve":
            trimmed = entity.find("BasisCurve")
            if "ref" in trimmed.attrib:
                trimmed = self.ref_check(trimmed)
            ifctrimmed = trimmed.attrib[self.type] if self.type in trimmed.attrib else trimmed.tag
            dim = self.IfcDimensionSize(trimmed, ifctrimmed)
        elif ifctype in ("IfcSurfaceCurve", "IfcIntersectionCurve", "IfcSeamCurve"):
            dim = 3
        elif ifctype == "IfcCartesianPoint":
            dim = len(re.split(r"\s+", str(entity.attrib["Coordinates"])))
        elif ifctype == "IfcPointOnCurve":
            curve = entity.find("BasisCurve")
            if "ref" in curve.attrib:
                curve = self.ref_check(curve)
            ifccurve = curve.attrib[self.type] if self.type in curve.attrib else curve.tag
            dim = self.IfcDimensionSize(curve, ifccurve)
        elif ifctype == "IfcPointOnSurface":
            surface = entity.find("BasisSurface")
            if "ref" in surface.attrib:
                surface = self.ref_check(surface)
            ifcsurface = surface.attrib[self.type] if self.type in surface.attrib else surface.tag
            dim = self.IfcDimensionSize(surface, ifcsurface)
        elif self.attr_check(ifctype, "IfcSurface"):
            dim = 3
        else:
            #ifc type is unknown
            dim = 0

        return dim


    def IfcNormalise(self, values):
        """
        Normalizes a vector.
        Input: A vector.
        Output: A normalized vector.
        """
        magnitude = 0.0
        for val in values:
            magnitude = magnitude + float(val) * float(val)
        magnitude = math.sqrt(magnitude)
        for i, val in enumerate(values):
            values[i] = float(val) / magnitude
        return values


    def IfcConstraintsParamBSpline(self, degree, upper, multiplicities, knots):
        """
        Checks if the constraints for a BSpline are fullfilled:
            I. Degree ≤ 1.
            II. Upper index on knots ≤ 2.
            III. Upper index on control points ≤ degree.
            IV. Sum of knot multiplicities = degree + (upper index on control points) + 2.
            V. For the first and last knot the multiplicity is bounded by 1 and (degree+1).
            VI. For all other knots the knot multiplicity is bounded by 1 and degree.
            VII. The consecutive knots are increasing in value.
        Input: Degree, Upper, Multiplicities, Knots.
        Output: A boolean value; True if all conditions are fullfilled, False otherwise.
        """
        result = True
        sum_mult = 0

        for mult in multiplicities:
            sum_mult = sum_mult + int(mult)

        if (
            degree < 1
            or len(multiplicities) < 2
            or upper < degree
            or sum_mult != degree + upper + 2
            or int(multiplicities[0]) > degree + 1
        ):
            result = False
            return result

        for i, mult in enumerate(multiplicities):
            if int(mult) < 1:
                result = False
                return result
            if i >= 1:
                if float(knots[i]) <= float(knots[i - 1]):
                    result = False
                    return result
            if i == 0 or i == len(multiplicities) - 1:
                if int(mult) > degree + 1:
                    result = False
                    return result
            else:
                if int(mult) > degree:
                    result = False
                    return result

        return result


    def IfcTaperedSweptAreaProfiles(self, start, end):
        """
        Checks whether the start and end profile in a tapered extrusion are topologically similar.
        Input: StartArea and EndArea.
        Output: Boolean value: TRUE, if conditions are fullfilled.
        """
        result = False

        if self.attr_check(start.attrib[self.type], "IfcParameterizedProfileDef"):
            if self.attr_check(end.attrib[self.type], "IfcDerivedProfileDef"):
                parent = end.find("ParentProfile")
                if "ref" in parent.attrib:
                    parent = self.ref_check(parent)
                if "id" in start.attrib:
                    start_id = start.attrib["id"]
                else:
                    start_id = start.attrib["ref"]
                if "id" in parent.attrib:
                    parent_id = parent.attrib["id"]
                else:
                    parent_id = parent.attrib["ref"]
                result = bool(parent_id == start_id)

            else:
                starting = start.attrib[self.type] if self.type in start.attrib else start.tag
                ending = end.attrib[self.type] if self.type in end.attrib else end.tag
                result = bool(starting == ending)

        else:
            if self.attr_check(end.attrib[self.type], "IfcDerivedProfileDef"):
                parent = end.find("ParentProfile")
                if "ref" in parent.attrib:
                    parent = self.ref_check(parent)
                if "id" in start.attrib:
                    start_id = start.attrib["id"]
                else:
                    start_id = start.attrib["ref"]
                if "id" in parent.attrib:
                    parent_id = parent.attrib["id"]
                else:
                    parent_id = parent.attrib["ref"]
                result = bool(parent_id == start_id)
            else:
                result = False

        return result


    def IfcShapeRepresentationTypes(self, rep_type, items):
        """
        The function gets the representation type and the assigned set of representation items as
        input and verifies whether the correct items are assigned according to the representation
        type given.
        Input: A representation type and set of representation items
        Output: Boolean value: TRUE, if conditions are fullfilled.
        """
        rep_type = rep_type.lower()
        count = 0

        if rep_type == "point":
            for item in items:
                if self.attr_check(item.tag, "IfcPoint"):
                    count += 1
        elif rep_type == "pointcloud":
            for item in items:
                if self.attr_check(item.tag, "IfcCartesianPointList3D"):
                    count += 1
        elif rep_type == "curve":
            for item in items:
                if self.attr_check(item.tag, "IfcCurve"):
                    count += 1
        elif rep_type == "curve2d":
            for item in items:
                if self.attr_check(item.tag, "IfcCurve"):
                    if "ref" in item.attrib:
                        item = self.ref_check(item)
                    dim = self.IfcDimensionSize(item, item.tag)
                    if dim == 2:
                        count += 1
        elif rep_type == "curve3d":
            for item in items:
                if self.attr_check(item.tag, "IfcCurve"):
                    if "ref" in item.attrib:
                        item = self.ref_check(item)
                    dim = self.IfcDimensionSize(item, item.tag)
                    if dim == 3:
                        count += 1
        elif rep_type == "surface":
            for item in items:
                if self.attr_check(item.tag, "IfcSurface"):
                    count += 1
        elif rep_type == "surface2d":
            for item in items:
                if self.attr_check(item.tag, "IfcSurface"):
                    if "ref" in item.attrib:
                        item = self.ref_check(item)
                    dim = self.IfcDimensionSize(item, item.tag)
                    if dim == 2:
                        count += 1
        elif rep_type == "surface3d":
            for item in items:
                if self.attr_check(item.tag, "IfcSurface"):
                    if "ref" in item.attrib:
                        item = self.ref_check(item)
                    dim = self.IfcDimensionSize(item, item.tag)
                    if dim == 3:
                        count += 1
        elif rep_type == "fillarea":
            for item in items:
                if self.attr_check(item.tag, "IfcAnnotationFillArea"):
                    count += 1
        elif rep_type == "text":
            for item in items:
                if self.attr_check(item.tag, "IfcTextLiteral"):
                    count += 1
        elif rep_type == "advancedsurface":
            for item in items:
                if self.attr_check(item.tag, "IfcBSplineSurface"):
                    count += 1
        elif rep_type == "annotation2d":
            allowed_type = [
                "IfcPoint",
                "IfcCurve",
                "IfcGeometricCurveSet",
                "IfcAnnotationFillArea",
                "IfcTextLiteral",
            ]
            for item in items:
                if self.attr_list_check(item.tag, allowed_type):
                    count += 1
        elif rep_type == "geometricset":
            allowed_type = ["IfcGeometricSet", "IfcPoint", "IfcCurve", "IfcSurface"]
            for item in items:
                if self.attr_list_check(item.tag, allowed_type):
                    count += 1
        elif rep_type == "geometriccurveset":
            allowed_type = ["IfcGeometricCurveSet", "IfcGeometricSet", "IfcPoint", "IfcCurve"]
            for item in items:
                if self.attr_list_check(item.tag, allowed_type):
                    count += 1
            for item in items:
                if self.attr_check(item.tag, "IfcGeometricSet"):
                    if "ref" in item.attrib:
                        item = self.ref_check(item)
                    elements = item.find("Elements")
                    for element in elements:
                        if self.attr_check(element.tag, "IfcSurface"):
                            count = count - 1
                            break
        elif rep_type == "tessellation":
            for item in items:
                if self.attr_check(item.tag, "IfcTessellatedItem"):
                    count += 1
        elif rep_type == "surfaceorsolidmodel":
            allowed_type = [
                "IfcTessellatedItem",
                "IfcShellBasedSurfaceModel",
                "IfcFaceBasedSurfaceModel",
                "IfcSolidModel",
            ]
            for item in items:
                if self.attr_list_check(item.tag, allowed_type):
                    count += 1
        elif rep_type == "surfacemodel":
            allowed_type = [
                "IfcTessellatedItem",
                "IfcShellBasedSurfaceModel",
                "IfcFaceBasedSurfaceModel",
            ]
            for item in items:
                if self.attr_list_check(item.tag, allowed_type):
                    count += 1
        elif rep_type == "solidmodel":
            for item in items:
                if self.attr_check(item.tag, "IfcSolidModel"):
                    count += 1
        elif rep_type == "sweptsolid":
            allowed_type = ["IfcExtrudedAreaSolid", "IfcRevolvedAreaSolid"]
            for item in items:
                if item.tag in allowed_type:
                    count += 1
        elif rep_type == "advancedsweptsolid":
            allowed_type = ["IfcSweptAreaSolid", "IfcSweptDiskSolid"]
            for item in items:
                if self.attr_list_check(item.tag, allowed_type):
                    count += 1
        elif rep_type == "csg":
            allowed_type = ["IfcBooleanResult", "IfcCsgPrimitive3D", "IfcCsgSolid"]
            for item in items:
                if self.attr_list_check(item.tag, allowed_type):
                    count += 1
        elif rep_type == "clipping":
            allowed_type = ["IfcCsgSolid", "IfcBooleanClippingResult"]
            for item in items:
                if self.attr_list_check(item.tag, allowed_type):
                    count += 1
        elif rep_type == "brep":
            for item in items:
                if self.attr_check(item.tag, "IfcFacetedBrep"):
                    count += 1
        elif rep_type == "advancedbrep":
            for item in items:
                if self.attr_check(item.tag, "IfcManifoldSolidBrep"):
                    count += 1
        elif rep_type == "boundingbox":
            if len(items) > 1:
                count = 0
            else:
                for item in items:
                    if self.attr_check(item.tag, "IfcBoundingBox"):
                        count += 1
        elif rep_type == "sectionedspine":
            for item in items:
                if self.attr_check(item.tag, "IfcSectionedSpine"):
                    count += 1
        elif rep_type == "lightsource":
            for item in items:
                if self.attr_check(item.tag, "IfcLightSource"):
                    count += 1
        elif rep_type == "mappedrepresentation":
            for item in items:
                if self.attr_check(item.tag, "IfcMappedItem"):
                    count += 1
        else:
            count = "?"

        if count != "?":
            return count == len(items)
        else:
            return count


    def IfcTopologyRepresentationTypes(self, rep_type, items):
        """
        The function gets the representation type and the assigned set of representation items as
        input and verifies whether the correct items are assigned according to the representation
        type given.
        Input: A representation type and set of representation items
        Output: Boolean value: TRUE, if conditions are fullfilled.
        """
        rep_type = rep_type.lower()
        count = 0

        if rep_type == "vertex":
            for item in items:
                if self.attr_check(item.tag, "IfcVertex"):
                    count += 1
        elif rep_type == "edge":
            for item in items:
                if self.attr_check(item.tag, "IfcEdge"):
                    count += 1
        elif rep_type == "path":
            for item in items:
                if self.attr_check(item.tag, "IfcPath"):
                    count += 1
        elif rep_type == "face":
            for item in items:
                if self.attr_check(item.tag, "IfcFace"):
                    count += 1
        elif rep_type == "shell":
            allowed_type = ["IfcOpenShell", "IfcClosedShell"]
            for item in items:
                if self.attr_list_check(item.tag, allowed_type):
                    count += 1
        else:
            count = "?"

        if count != "?":
            return count == len(items)
        else:
            return count


    def IfcCorrectObjectAssignment(self, constraint, objects):
        """
        This function checks, whether the correct object types are used within the IfcRelAssigns
        relationship (or one of its subtypes).
        Input: A constraint and set of objects
        Output: Boolean value: TRUE, if constraint is fullfilled.
        """
        constraint = constraint.lower()
        count = 0

        if constraint == "notdefined":
            return True
        elif constraint == "product":
            for item in objects:
                if self.attr_check(item.tag, "IfcProduct"):
                    count += 1
        elif constraint == "process":
            for item in objects:
                if self.attr_check(item.tag, "IfcProcess"):
                    count += 1
        elif constraint == "control":
            for item in objects:
                if self.attr_check(item.tag, "IfcControl"):
                    count += 1
        elif constraint == "resource":
            for item in objects:
                if self.attr_check(item.tag, "IfcResource"):
                    count += 1
        elif constraint == "actor":
            for item in objects:
                if self.attr_check(item.tag, "IfcActor"):
                    count += 1
        elif constraint == "group":
            for item in objects:
                if self.attr_check(item.tag, "IfcGroup"):
                    count += 1
        elif constraint == "project":
            for item in objects:
                if self.attr_check(item.tag, "IfcProject"):
                    count += 1
        else:
            count = "?"

        if count != "?":
            return count == len(objects)
        else:
            return count


    def IfcCorrectDimensions(self, unit, dim):
        """
        This function checks, whether the measurement units have the correct dimension.
        Input: A measure unit and a dimension list or object.
        Output: Boolean value: TRUE, if the correct dimensions are given.
        """
        unit = unit.lower()
        if isinstance(dim, list):
            dim_list = dim
        else:
            dim_list = []
            dim_list.append(int(dim.attrib["LengthExponent"]))
            dim_list.append(int(dim.attrib["MassExponent"]))
            dim_list.append(int(dim.attrib["TimeExponent"]))
            dim_list.append(int(dim.attrib["ElectricCurrentExponent"]))
            dim_list.append(int(dim.attrib["ThermodynamicTemperatureExponent"]))
            dim_list.append(int(dim.attrib["AmountOfSubstanceExponent"]))
            dim_list.append(int(dim.attrib["LuminousIntensityExponent"]))
        count = 0

        if unit == "lengthunit":
            result = dim_list == [1, 0, 0, 0, 0, 0, 0]
        elif unit == "massunit":
            result = dim_list == [0, 1, 0, 0, 0, 0, 0]
        elif unit == "timeunit":
            result = dim_list == [0, 0, 1, 0, 0, 0, 0]
        elif unit == "electriccurrentunit":
            result = dim_list == [0, 0, 0, 1, 0, 0, 0]
        elif unit == "thermodynamictemperatureunit":
            result = dim_list == [0, 0, 0, 0, 1, 0, 0]
        elif unit == "amountofsubstanceunit":
            result = dim_list == [0, 0, 0, 0, 0, 1, 0]
        elif unit == "luminousintensityunit":
            result = dim_list == [0, 0, 0, 0, 0, 0, 1]
        elif unit == "planeangleunit":
            result = dim_list == [0, 0, 0, 0, 0, 0, 0]
        elif unit == "solidangleunit":
            result = dim_list == [0, 0, 0, 0, 0, 0, 0]
        elif unit == "areaunit":
            result = dim_list == [2, 0, 0, 0, 0, 0, 0]
        elif unit == "volumeunit":
            result = dim_list == [3, 0, 0, 0, 0, 0, 0]
        elif unit == "absorbeddoseunit":
            result = dim_list == [2, 0, -2, 0, 0, 0, 0]
        elif unit == "radioactivityunit":
            result = dim_list == [0, 0, -1, 0, 0, 0, 0]
        elif unit == "electriccapacitanceunit":
            result = dim_list == [-2, -1, 4, 2, 0, 0, 0]
        elif unit == "doseequivalentunit":
            result = dim_list == [2, 0, -2, 0, 0, 0, 0]
        elif unit == "electricchargeunit":
            result = dim_list == [0, 0, 1, 1, 0, 0, 0]
        elif unit == "electricconductanceunit":
            result = dim_list == [-2, -1, 3, 2, 0, 0, 0]
        elif unit == "electricvoltageunit":
            result = dim_list == [2, 1, -3, -1, 0, 0, 0]
        elif unit == "electricresistanceunit":
            result = dim_list == [2, 1, -3, -2, 0, 0, 0]
        elif unit == "energyunit":
            result = dim_list == [2, 1, -2, 0, 0, 0, 0]
        elif unit == "forceunit":
            result = dim_list == [1, 1, -2, 0, 0, 0, 0]
        elif unit == "frequencyunit":
            result = dim_list == [0, 0, -1, 0, 0, 0, 0]
        elif unit == "inductanceunit":
            result = dim_list == [2, 1, -2, -2, 0, 0, 0]
        elif unit == "illuminanceunit":
            result = dim_list == [-2, 0, 0, 0, 0, 0, 1]
        elif unit == "luminousfluxunit":
            result = dim_list == [0, 0, 0, 0, 0, 0, 1]
        elif unit == "magneticfluxunit":
            result = dim_list == [2, 1, -2, -1, 0, 0, 0]
        elif unit == "magneticfluxdensityunit":
            result = dim_list == [0, 1, -2, -1, 0, 0, 0]
        elif unit == "powerunit":
            result = dim_list == [2, 1, -3, 0, 0, 0, 0]
        elif unit == "pressureunit":
            result = dim_list == [-1, 1, -2, 0, 0, 0, 0]
        else:
            count = "?"

        if count != "?":
            return result
        else:
            return count


    def IfcDimensionsForSiUnit(self, unit):
        """
        The function returns the dimensional exponents of the given SI-unit.
        Input: Name of the unit
        Output: Dimensional exponents
        """
        unit = unit.lower()

        if unit == "metre":
            dim_exp = [1, 0, 0, 0, 0, 0, 0]
        elif unit == "square_metre":
            dim_exp = [2, 0, 0, 0, 0, 0, 0]
        elif unit == "cubic_metre":
            dim_exp = [3, 0, 0, 0, 0, 0, 0]
        elif unit == "gram":
            dim_exp = [0, 1, 0, 0, 0, 0, 0]
        elif unit == "second":
            dim_exp = [0, 0, 1, 0, 0, 0, 0]
        elif unit == "ampere":
            dim_exp = [0, 0, 0, 1, 0, 0, 0]
        elif unit == "kelvin":
            dim_exp = [0, 0, 0, 0, 1, 0, 0]
        elif unit == "mole":
            dim_exp = [0, 0, 0, 0, 0, 1, 0]
        elif unit == "candela":
            dim_exp = [0, 0, 0, 0, 0, 0, 1]
        elif unit == "radian":
            dim_exp = [0, 0, 0, 0, 0, 0, 0]
        elif unit == "steradian":
            dim_exp = [0, 0, 0, 0, 0, 0, 0]
        elif unit == "newton":
            dim_exp = [1, 1, -2, 0, 0, 0, 0]
        elif unit == "hertz":
            dim_exp = [0, 0, -1, 0, 0, 0, 0]
        elif unit == "joule":
            dim_exp = [2, 1, -2, 0, 0, 0, 0]
        elif unit == "watt":
            dim_exp = [2, 1, -3, 0, 0, 0, 0]
        elif unit == "pascal":
            dim_exp = [-1, 1, -2, 0, 0, 0, 0]
        elif unit == "gray":
            dim_exp = [2, 0, -2, 0, 0, 0, 0]
        elif unit == "becquerel":
            dim_exp = [0, 0, -1, 0, 0, 0, 0]
        elif unit == "farad":
            dim_exp = [-2, -1, 4, 2, 0, 0, 0]
        elif unit == "siever":
            dim_exp = [2, 0, -2, 0, 0, 0, 0]
        elif unit == "coulomb":
            dim_exp = [0, 0, 1, 1, 0, 0, 0]
        elif unit == "siemens":
            dim_exp = [-2, -1, 3, 2, 0, 0, 0]
        elif unit == "volt":
            dim_exp = [2, 1, -3, -1, 0, 0, 0]
        elif unit == "ohm":
            dim_exp = [2, 1, -3, -2, 0, 0, 0]
        elif unit == "henry":
            dim_exp = [2, 1, -2, -2, 0, 0, 0]
        elif unit == "lux":
            dim_exp = [-2, 0, 0, 0, 0, 0, 1]
        elif unit == "lumen":
            dim_exp = [0, 0, 0, 0, 0, 0, 1]
        elif unit == "weber":
            dim_exp = [2, 1, -2, -1, 0, 0, 0]
        elif unit == "tesla":
            dim_exp = [0, 1, -2, -1, 0, 0, 0]
        elif unit == "degree_celsius":
            dim_exp = [0, 0, 0, 0, 1, 0, 0]
        else:
            dim_exp = [0, 0, 0, 0, 0, 0, 0]

        return dim_exp


    def IfcGetBasisSurface(self, curve):
        """
        The function returns the surface on which a curve lies on.
        Input: IfcCurveOnSurface
        Output: Set of IfcSurface
        """
        if self.type in curve.attrib:
            curve_type = curve.attrib[self.type]
        else:
            curve_type = curve.tag

        surfs = []
        if self.attr_check(curve_type, "IfcPcurve"):
            curve = curve.find("BasisSurface")
            if "ref" in curve.attrib:
                curve = self.ref_check(curve)
            surfs.append(curve)
        elif self.attr_check(curve_type, "IfcSurfaceCurve"):
            geometry = curve.find("AssociatedGeometry")
            for geom in geometry:
                if "ref" in geom.attrib:
                    geom = self.ref_check(geom)
                surfs.append(geom)
        elif self.attr_check(curve_type, "IfcCompositeCurveOnSurface"):
            segments = curve.find("Segments")
            parent = segments[0].find("ParentCurve")
            if "ref" in parent.attrib:
                parent = self.ref_check(parent)
            if "id" in parent.attrib:
                parent_id = parent.attrib["id"]
            else:
                parent_id = parent.attrib["ref"]
            surfs.append(self.IfcGetBasisSurface(parent))
            for i, seg in enumerate(segments):
                if i > 0:
                    current_parent = seg.find("ParentCurve")
                    if "ref" in current_parent.attrib:
                        current_parent = self.ref_check(current_parent)
                    if "id" in current_parent.attrib:
                        current_parent_id = current_parent.attrib["id"]
                    else:
                        current_parent_id = current_parent.attrib["ref"]
                    current_surfs = [self.IfcGetBasisSurface(current_parent)]
                    if (
                        current_parent_id != parent_id
                        and not self.elements_equal(parent, current_parent)
                        and surfs != current_surfs
                    ):
                        surfs = []
                        break

        return surfs

    ##############################
    ###General rules functions####
    ##############################

    """
    All methods relating to given formal propositions have the same parameters and same structure,
    although some might not be used. Due to the automated call of these methods, it is not
    further "optimized":

    Parameters
    ----------
    entity: Entity
        The current entity.

    ifcname: str
        The name of the ifc type of the current entity.

    called_entity: str(?)
        The entity that called the current "entity", default value it is not called.


    Returns/Output
    ----------
    It returns a warning/error message, if the rule/formal proposition does not apply to the
    current entity.
    """

    def AllPointsSameDim(self, entity, ifcname, called_entity=None):
        """Get the dimensionality of the first point/child and then check if all other points have
        the same dimensionality.
        ----------
        This is used in IfcPolyLoop."""
        polygon = entity.find("Polygon")
        if "ref" in polygon.attrib:
            polygon = self.ref_check(polygon)
        if "ref" in polygon[0].attrib:
            polygon[0] = self.ref_check(polygon[0])
        dim = len(re.split(r"\s+", polygon[0].attrib["Coordinates"]))
        for child in polygon:
            if "ref" in child.attrib:
                child = self.ref_check(child)
            if len(re.split(r"\s+", str(child.attrib["Coordinates"]))) != dim:
                return "Not all points have the same dimensionality"


    def AllowedElements(self, entity, ifcname, called_entity=None):
        """Checks if material information is assigned to correct objects.
        ----------
        This is used in IfcRelAssociatesMaterial."""
        rel_objects = entity.find("RelatedObjects")
        allowed_elements = [
            "IfcElement",
            "IfcElementType",
            "IfcWindowStyle",
            "IfcDoorStyle",
            "IfcStructuralMember",
        ]
        for rel_object in rel_objects:
            if not self.attr_list_check(rel_object.tag, allowed_elements):
                return (
                    "Material information cannot be associated to the object "
                    + str(rel_object.tag)
                )


    def AllowedRelatedElements(self, entity, ifcname, called_entity=None):
        """Checks if the related element types are allowed.
        ----------
        This is used in IfcRelReferencedInSpatialStructure."""
        error_msg = "The relationship object shall not be used to include other spatial "\
            "structure elements into a spatial structure element. The hierarchy of "\
            "the spatial structure is defined using IfcRelAggregates. Exception: "\
            "An IfcSpace can be referenced by another spatial structure element, "\
            "in particular by an IfcSpatialZone"
        rel_elem = entity.find("RelatedElements")
        if rel_elem is not None:
            for elem in rel_elem:
                if self.attr_check(elem.tag, "IfcSpatialStructureElement") and elem.tag != "IfcSpace":
                    return error_msg

        elif called_entity == "RelatedElements":
            rel_elem = entity.getparent().getparent()
            rel_elem_type = (
                rel_elem.attrib[self.type] if self.type in rel_elem.attrib else rel_elem.tag
            )
            if (
                self.attr_check(rel_elem_type, "IfcSpatialStructureElement")
                and rel_elem_type != "IfcSpace"
            ):
                return error_msg
        else:
            identifier = entity.attrib["id"]
            referenced = self.tree.findall(f".//*[@ref='{identifier}']")
            if len(referenced) > 0:
                for ref in referenced:
                    if ref.getparent().tag == "HasProjections":
                        ref_type = (
                            ref.getparent().getparent().attrib[self.type]
                            if self.type in ref.getparent().getparent()
                            else ref.getparent().getparent().tag
                        )
                        if (
                            self.attr_check(ref_type, "IfcSpatialStructureElement")
                            and ref_type != "IfcSpace"
                        ):
                            return error_msg


    def ApplicableEdgeCurves(self, entity, ifcname, called_entity=None):
        """Checks if the given curve type is allowed.
        ----------
        This is used in IfcAdvancedFace."""
        bounds = entity.find("Bounds")
        error_msg = "The types of curve used to define the geometry of edges shall be "\
            "restricted to IfcLine, IfcConic, IfcPolyline, or IfcBSplineCurve"
        for b in bounds:
            bound = b.find("Bound")
            if "ref" in bound.attrib:
                bound = self.ref_check(bound)
            bound_type = bound.attrib[self.type] if self.type in bound.attrib else bound.tag
            if bound_type != "IfcEdgeLoop":
                return error_msg
            else:
                edges = bound.find("EdgeList")
                for edge in edges:
                    allowed_geo = ["IfcLine", "IfcConic", "IfcPolyline", "IfcBSplineCurve"]
                    edge_elem = edge.find("EdgeElement")
                    if "ref" in edge_elem.attrib:
                        edge_elem = self.ref_check(edge_elem)
                    edge_geo = edge_elem.find("EdgeGeometry")
                    if "ref" in edge_geo.attrib:
                        edge_geo = self.ref_check(edge_geo)
                    edge_geo = (
                        edge_geo.attrib[self.type] if self.type in edge_geo.attrib else edge_geo.tag
                    )
                    if not self.attr_list_check(edge_geo, allowed_geo):
                        return error_msg


    def ApplicableItem(self, entity, ifcname, called_entity=None):
        """Checks if a styled item is not styled by another styled item.
        ----------
        This is used in IfcStyledItem."""
        item = entity.getparent() if called_entity == "Item" else entity.find("Item")
        error_msg = "A styled item cannot be styled by another styled item"
        if item is not None:
            if "ref" in item.attrib:
                item = self.ref_check(item)
            item_type = item.attrib[self.type] if self.type in item.attrib else item.tag
            if item_type == "IfcStyledItem":
                return error_msg
        else:
            identifier = entity.attrib["id"]
            referenced = self.tree.findall(f".//*[@ref='{identifier}']")
            if len(referenced) > 0:
                for ref in referenced:
                    if ref.getparent().tag == "StyledByItem":
                        if ref.attrib[self.type] == "IfcStyledItem":
                            return error_msg


    def ApplicableItems(self, entity, ifcname, called_entity=None):
        """Checks if the assigned items have the correct representation.
        ----------
        This is used in IfcPresentationLayerAssignment."""
        allowed_items = [
            "IfcShapeRepresentation",
            "IfcGeometricRepresentationItem",
            "IfcMappedItem",
        ]
        error_msg = "The items within the set of AssignedItems that can be assigned to a "\
                        "presentation layer shall be geometric shape representation or "\
                        "representation items"
        items = entity.find("AssignedItems")
        if items is not None:
            if self.type in items.attrib:
                if not self.attr_list_check(items.attrib[self.type], allowed_items):
                    return error_msg
            else:
                for item in items:
                    if not self.attr_list_check(item.tag, allowed_items):
                        return error_msg
        else:
            if called_entity is not None:
                if entity.tag == "AssignedItems":
                    item = entity.getparent()
                else:
                    item = entity.getparent().getparent()
                item_type = item.attrib[self.type] if self.type in item.attrib else item.tag
                if not self.attr_list_check(item_type, allowed_items):
                    return error_msg

            identifier = entity.attrib["id"]
            referenced = self.tree.findall(f".//*[@ref='{identifier}']")
            if len(referenced) > 0:
                for ref in referenced:
                    if ref.tag == "LayerAssignment":
                        ref_type = (
                            ref.getparent().attrib[self.type]
                            if self.type in ref.getparent().attrib
                            else ref.getparent().tag
                        )
                        if not self.attr_list_check(ref_type, allowed_items):
                            return error_msg
                    elif ref.getparent().tag == "LayerAssignments":
                        ref_type = (
                            ref.getparent().getparent().attrib[self.type]
                            if self.type in ref.getparent().getparent().attrib
                            else ref.getparent().getparent().tag
                        )
                        if not self.attr_list_check(ref_type, allowed_items):
                            return error_msg


    def ApplicableMappedRepr(self, entity, ifcname, called_entity=None):
        """Checks if a correct mapped representation is given.
        ----------
        This is used in IfcRepresentationMap."""
        mapped_repr = (
            entity.getparent()
            if called_entity == "MappedRepresentation"
            else entity.find("MappedRepresentation")
        )
        error_msg = "Only representations of type IfcShapeRepresentation, or "\
                    "IfcTopologyRepresentation are allowed as MappedRepresentation"
        if mapped_repr is not None:
            if "ref" in mapped_repr.attrib:
                mapped_repr = self.ref_check(mapped_repr)
            mapped_repr_type = (
                mapped_repr.attrib[self.type]
                if self.type in mapped_repr.attrib
                else mapped_repr.tag
            )
            if not self.attr_check(mapped_repr_type, "IfcShapeModel"):
                return error_msg
        else:
            identifier = entity.attrib["id"]
            referenced = self.tree.findall(f".//*[@ref='{identifier}']")
            if len(referenced) > 0:
                for ref in referenced:
                    if ref.tag == "RepresentationMap":
                        if not self.attr_check(ref.getparent().attrib[self.type], "IfcShapeModel"):
                            return error_msg


    def ApplicableOccurrence(self, entity, ifcname, called_entity=None):
        """Checks if the product type/style is assigned to an object being a subtype of IfcProduct.
        ----------
        This is used in IfcTypeProduct."""
        types = entity.find("Types")
        if types is not None:
            rel_object = types[0].find("RelatedObjects")
            for obj in rel_object:
                rel_type = obj.tag
                if "IfcProduct" not in self.entities[rel_type]["supertypes"]:
                    return "The product type (or style), if assigned to an object, shall only be "\
                        "assigned to object being a sub type of IfcProduct"


    def ApplicableOnlyToItems(self, entity, ifcname, called_entity=None):
        """Checks if the IfcPresentationLayerWithStyle is only applied to items.
        ----------
        This is used in IfcPresentationLayerWithStyle."""
        allowed_items = ["IfcGeometricRepresentationItem", "IfcMappedItem"]
        items = entity.find("AssignedItems")
        for item in items:
            if not self.attr_list_check(item.tag, allowed_items):
                return "The IfcPresentationLayerWithStyle shall only be used to assign subtypes "\
                    "of IfcGeometricRepresentationItem's and to IfcMappedItem. There shall be no "\
                    "instance of subtypes of IfcRepresentation in the set of AssignedItem's"


    def ApplicableSurface(self, entity, ifcname, called_entity=None):
        """Checks if the face geometry has an allowed type.
        ----------
        This is used in IfcAdvancedFace."""
        allowed_surfaces = ["IfcElementarySurface", "IfcSweptSurface", "IfcBSplineSurface"]
        surface = entity.find("FaceSurface")
        if "ref" in surface.attrib:
            surface = self.ref_check(surface)
        surface_type = surface.attrib[self.type] if self.type in surface.attrib else surface.tag
        if not self.attr_list_check(surface_type, allowed_surfaces):
            return "The geometry used in the definition of the face shall be restricted. "\
                "The face geometry shall be an IfcElementarySurface, IfcSweptSurface, or "\
                "IfcBSplineSurface"


    def ApplicableToType(self, entity, ifcname, called_entity=None):
        """Checks if the panel properties are applied to the corresponding entities.
        ----------
        This is used in IfcDoorPanelProperties & IfcWindowPanelProperties."""
        if ifcname == "IfcDoorPanelProperties":
            error_msg = "The IfcDoorPanelProperties shall only be used in the context of an "\
                "IfcDoorType (or IfcDoorStyle)"
            defines = entity.find("DefinesType")
            if defines is None:
                return error_msg
            else:
                for define in defines:
                    if define.tag != "IfcDoorType" and define.tag != "IfcDoorStyle":
                        return error_msg
        elif ifcname == "IfcWindowPanelProperties":
            error_msg = "The IfcWindowPanelProperties shall only be used in the context of an "\
                "IfcWindowType (or IfcWindowStyle)"
            defines = entity.find("DefinesType")
            if defines is None:
                return error_msg
            else:
                for define in defines:
                    if define.tag != "IfcWindowType" and define.tag != "IfcWindowStyle":
                        return error_msg


    def AvoidInconsistentSequence(self, entity, ifcname, called_entity=None):
        """Checks if the relating and related process do not point to the same instance.
        ----------
        This is used in IfcRelSequence."""
        if called_entity == "RelatingProcess":
            relating = entity.getparent().getparent()
        else:
            relating = entity.find("RelatingProcess")
            if relating is None:
                identifier = entity.attrib["id"]
                referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                if len(referenced) > 0:
                    for ref in referenced:
                        if ref.getparent().tag == "IsPredecessorTo":
                            relating = ref.getparent().getparent()
        if "ref" in relating.attrib:
            relating = self.ref_check(relating)
        if called_entity == "RelatedProcess":
            related = entity.getparent().getparent()
        else:
            related = entity.find("RelatedProcess")
            if related is None:
                identifier = entity.attrib["id"]
                referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                if len(referenced) > 0:
                    for ref in referenced:
                        if ref.getparent().tag == "IsSuccessorFrom":
                            related = ref.getparent().getparent()
        if "ref" in related.attrib:
            related = self.ref_check(related)
        equal = self.elements_equal(relating, related)
        if equal or relating.attrib["id"] == related.attrib["id"]:
            return "The RelatingProcess shall not point to the same instance as the RelatedProcess"


    def Axis1Is2D(self, entity, ifcname, called_entity=None):
        """Checks if the first axis is 2D.
        ----------
        This is used in IfcCartesianTransformationOperator2D."""
        axis1 = entity.find("Axis1")
        if axis1 is not None:
            if "ref" in axis1.attrib:
                axis1 = self.ref_check(axis1)
            if len(re.split(r"\s+", axis1.attrib["DirectionRatios"])) != 2:
                return "Axis 1 has to be 2D"


    def Axis1Is3D(self, entity, ifcname, called_entity=None):
        """Checks if the first axis is 3D.
        ----------
        This is used in IfcCartesianTransformationOperator3D."""
        axis1 = entity.find("Axis1")
        if axis1 is not None:
            if "ref" in axis1.attrib:
                axis1 = self.ref_check(axis1)
            if len(re.split(r"\s+", axis1.attrib["DirectionRatios"])) != 3:
                return "Axis 1 has to be 3D"


    def Axis2Is2D(self, entity, ifcname, called_entity=None):
        """Checks if the second axis is 2D.
        ----------
        This is used in IfcCartesianTransformationOperator2D."""
        axis2 = entity.find("Axis2")
        if axis2 is not None:
            if "ref" in axis2.attrib:
                axis2 = self.ref_check(axis2)
            if len(re.split(r"\s+", axis2.attrib["DirectionRatios"])) != 2:
                return "Axis 2 has to be 2D"


    def Axis2Is3D(self, entity, ifcname, called_entity=None):
        """Checks if the second axis is 3D.
        ----------
        This is used in IfcCartesianTransformationOperator3D."""
        axis2 = entity.find("Axis2")
        if axis2 is not None:
            if "ref" in axis2.attrib:
                axis2 = self.ref_check(axis2)
            if len(re.split(r"\s+", axis2.attrib["DirectionRatios"])) != 3:
                return "Axis 2 has to be 3D"


    def Axis3Is3D(self, entity, ifcname, called_entity=None):
        """Checks if the third axis is 3D.
        ----------
        This is used in IfcCartesianTransformationOperator3D."""
        axis3 = entity.find("Axis3")
        if axis3 is not None:
            if "ref" in axis3.attrib:
                axis3 = self.ref_check(axis3)
            if len(re.split(r"\s+", axis3.attrib["DirectionRatios"])) != 3:
                return "Axis 3 has to be 3D"


    def AxisAndRefDirProvision(self, entity, ifcname, called_entity=None):
        """Checks if both, axis and refdirection, are provided or none of them.
        ----------
        This is used in IfcAxis2Placement3D."""
        axis = entity.find("Axis")
        refdirection = entity.find("RefDirection")
        if (axis is None and refdirection is not None) or (
            axis is not None and refdirection is None
        ):
            return "Either Axis and RefDirection have to be provided or none of both"


    def AxisDirectionInXY(self, entity, ifcname, called_entity=None):
        """Checks if the z-coordinate of the direction has value 0.
        ----------
        This is used in IfcRevolvedAreaSolid."""
        axis = entity.find("Axis")
        if "ref" in axis.attrib:
            axis = self.ref_check(axis)
        dir_axis = axis.find("Axis")
        if "ref" in dir_axis.attrib:
            dir_axis = self.ref_check(dir_axis)
        coordinates = re.split(r"\s+", dir_axis.attrib["DirectionRatios"])
        if float(coordinates[2]) != 0.0:
            return "The Z-coordinate has to have value 0.0"


    def AxisIs3D(self, entity, ifcname, called_entity=None):
        """Checks if the axis is 3D.
        ----------
        This is used in IfcAxis1Placement & IfcAxis2Placement3D."""
        axis = entity.find("Axis")
        if axis is not None:
            if "ref" in axis.attrib:
                axis = self.ref_check(axis)
            if len(re.split(r"\s+", axis.attrib["DirectionRatios"])) != 3:
                return "Axis has to be 3D"


    def AxisStartInXY(self, entity, ifcname, called_entity=None):
        """Checks if the z-coordinate of the start location is 0.
        ----------
        This is used in IfcRevolvedAreaSolid."""
        axis = entity.find("Axis")
        if "ref" in axis.attrib:
            axis = self.ref_check(axis)
        location = axis.find("Location")
        if "ref" in location.attrib:
            location = self.ref_check(location)
        coordinates = re.split(r"\s+", location.attrib["Coordinates"])
        if float(coordinates[2]) != 0.0:
            return "The Z-coordinate has to have value 0.0"


    def AxisToRefDirPosition(self, entity, ifcname, called_entity=None):
        """Checks if the axis and refdirection are neither parallel nor anti-parallel.
        ----------
        This is used in IfcAxis2Placement3D."""
        axis = entity.find("Axis")
        direction = entity.find("RefDirection")
        if axis is not None and direction is not None:
            if "ref" in axis.attrib:
                axis = self.ref_check(axis)
            if "ref" in direction.attrib:
                direction = self.ref_check(direction)
            axis = re.split(r"\s+", axis.attrib["DirectionRatios"])
            direction = re.split(r"\s+", direction.attrib["DirectionRatios"])
            axis = self.IfcNormalise(axis)
            direction = self.IfcNormalise(direction)

            res1 = axis[1] * direction[2] - axis[2] * direction[1]
            res2 = axis[2] * direction[0] - axis[0] * direction[2]
            res3 = axis[0] * direction[1] - axis[1] * direction[0]
            magnitude = res1 * res1 + res2 * res2 + res3 * res3
            if magnitude <= 0:
                return "The Axis and RefDirection shall not be parallel or anti-parallel"


    def BendingShapeCodeProvided(self, entity, ifcname, called_entity=None):
        """Checks if a bending shape code is provided.
        ----------
        This is used in IfcReinforcingBarType & IfcReinforcingMeshType."""
        parameters = entity.find("BendingParameters")
        if parameters is not None:
            if "ref" in parameters.attrib:
                parameters = self.ref_check(parameters)
            if "BendingShapeCode" not in entity.attrib or entity.attrib["BendingShapeCode"] == "":
                return "Bending parameters must be accompanied by a shape code"


    def BoundaryDim(self, entity, ifcname, called_entity=None):
        """Checks if the bounding polyline is 2D.
        ----------
        This is used in IfcPolygonalBoundedHalfSpace."""
        boundary = entity.find("PolygonalBoundary")
        if "ref" in boundary.attrib:
            boundary = self.ref_check(boundary)
        boundary_type = boundary.attrib[self.type] if self.type in boundary.attrib else boundary.tag
        dim = self.IfcDimensionSize(boundary, boundary_type)
        if dim != 2:
            return "The bounding polyline should have the dimensionality of 2"


    def BoundaryType(self, entity, ifcname, called_entity=None):
        """Checks if the bounced curve has an allowed type.
        ----------
        This is used in IfcPolygonalBoundedHalfSpace."""
        allowed_boundaries = ["IfcPolyline", "IfcCompositeCurve"]
        boundary = entity.find("PolygonalBoundary")
        if "ref" in boundary.attrib:
            boundary = self.ref_check(boundary).attrib[self.type]
        boundary_type = boundary.attrib[self.type] if self.type in boundary.attrib else boundary.tag
        if not self.attr_list_check(boundary_type, allowed_boundaries):
            return "Only bounded curves of type IfcCompositeCurve, or IfcPolyline are valid "\
                "boundaries"


    def CP2Dor3D(self, entity, ifcname, called_entity=None):
        """Checks if the points are 2D or 3D.
        ----------
        This is used in IfcCartesianPoint."""
        coord = re.split(r"\s+", entity.attrib["Coordinates"])
        if len(coord) != 2 and len(coord) != 3:
            return "Only two or three dimensional points are in scope"


    def Consecutive(self, entity, ifcname, called_entity=None):
        """Checks if the indexed segments are consecutive.
        ----------
        This is used in IfcIndexedPolyCurve."""
        segments = entity.find("Segments")
        if segments is not None:
            for i in range(len(segments) - 1):
                current_segment = re.split(r"\s+", segments[i].text)
                next_segment = re.split(r"\s+", segments[i + 1].text)
                if current_segment[-1] != next_segment[0]:
                    return "If a list of indexed segments is provided, they need to be "\
                        "consecutive, meaning that the last index of all, but the last, "\
                        "segments shall be identical with the first index of the next segment"


    def ConsistentBSpline(self, entity, ifcname, called_entity=None):
        """Checks if the parametrisation of the B-spline are consistent.
        ----------
        This is used in IfcBSplineCurveWithKnots."""
        degree = int(entity.attrib["Degree"])
        upper = len(entity.find("ControlPointsList")) - 1
        multiplicities = re.split(r"\s+", entity.attrib["KnotMultiplicities"])
        knots = re.split(r"\s+", entity.attrib["Knots"])
        conditions = self.IfcConstraintsParamBSpline(degree, upper, multiplicities, knots)
        if not conditions:
            return "The function IfcConstraintsParamBSpline returns TRUE if no inconsistencies "\
                "in the parametrisation of the B-spline are found"


    def ConsistentDim(self, entity, ifcname, called_entity=None):
        """Checks if every element has the same dimension.
        ----------
        This is used in IfcGeometricSet."""
        elements = entity.find("Elements")
        if "ref" in elements[0].attrib:
            elements[0] = self.ref_check(elements[0])
        dim_original = self.IfcDimensionSize(elements[0], elements[0].tag)
        for elem in elements:
            if "ref" in elem.attrib:
                elem = self.ref_check(elem)
            dim_now = self.IfcDimensionSize(elem, elem.tag)
            if dim_original != dim_now:
                return "All elements within a geometric set shall have the same dimensionality"


    def ConsistentHatchStyleDef(self, entity, ifcname, called_entity=None):
        """Checks if the hatch style definitions are consistent.
        ----------
        This is used in IfcFillAreaStyle."""
        styles = entity.find("FillStyles")
        hatching = 0
        tiles = 0
        colour = 0
        external = 0
        for style in styles:
            if style.tag == "IfcFillAreaStyleHatching":
                hatching = hatching + 1
            elif style.tag == "IfcFillAreaStyleTiles":
                tiles = tiles + 1
            elif style.tag == "IfcExternallyDefinedHatchStyle":
                external = external + 1
            else:
                colour = colour + 1

        if external > 1 or colour > 1:
            result1 = False
        else:
            result1 = True
        if external == 1 and (hatching > 0 or tiles > 0 or colour > 0):
            result2 = False
        else:
            result2 = True
        if hatching > 0 and tiles > 0:
            result3 = False
        else:
            result3 = True

        if not result1 or not result2 or not result3:
            return "Either the fill area style contains a definition from an externally "\
                "defined hatch style, or from (one or many) fill area style hatchings or from "\
                "(one or many) fill area style tiles, but not a combination of those three types"


    def ConsistentProfileTypes(self, entity, ifcname, called_entity=None):
        """Checks if the given profile type is either area or curve for every section.
        ----------
        This is used in IfcSectionedSpine."""
        sections = entity.find("CrossSections")
        if "ref" in sections[0].attrib:
            sections[0] = self.ref_check(sections[0])
        profile_type = sections[0].attrib["ProfileType"]
        for sec in sections:
            if sec.attrib["ProfileType"] != profile_type:
                return "The profile type (either AREA or CURVE) shall be consistent within the "\
                    "list of the profiles defining the cross sections"


    def ConstPredefinedType(self, entity, ifcname, called_entity=None):
        """Checks if structural linear/planar action have a constant load distribution.
        ----------
        This is used in IfcStructuralLinearAction & IfcStructuralPlanarAction."""
        if entity.attrib["PredefinedType"].lower() != "const":
            if ifcname == "IfcStructuralLinearAction":
                return "This curve action subtype is restricted to constant load distribution "\
                    "over its domain"
            elif ifcname == "IfcStructuralPlanarAction":
                return "This surface action subtype is restricted to constant load distribution "\
                    "over its domain"


    def CorrectChangeAction(self, entity, ifcname, called_entity=None):
        """Checks if change action is only asserted if last modified date is defined
        (or set to notdefined).
        ----------
        This is used in IfcOwnerHistory."""
        if "LastModifiedDate" not in entity.attrib or entity.attrib["LastModifiedDate"] == "":
            if "ChangeAction" in entity.attrib:
                if not (
                    entity.attrib["ChangeAction"].lower() == "notdefined"
                    or entity.attrib["ChangeAction"].lower() == "nochange"
                ):
                    return "If ChangeAction is asserted and LastModifiedDate is not defined, "\
                        "ChangeAction must be set to NOTDEFINED"


    def CorrectContext(self, entity, ifcname, called_entity=None):
        """Checks if the correct context of items is provided.
        ----------
        This is used in IfcShapeRepresentation & IfcProject."""
        if ifcname == "IfcShapeRepresentation":
            context = entity.find("ContextOfItems")
            if "ref" in context.attrib:
                context = self.ref_check(context)
            context_type = context.attrib[self.type] if self.type in context.attrib else context.tag
            if not self.attr_check(context_type, "IfcGeometricRepresentationContext"):
                return "The context to which the IfcShapeRepresentation is assign, shall be of "\
                    "type IfcGeometricRepresentationContext"
        elif ifcname == "IfcProject":
            repr_contexts = entity.find("RepresentationContexts")
            if repr_contexts is not None:
                for context in repr_contexts:
                    if context.tag == "IfcGeometricRepresentationSubContext":
                        return "If a RepresentationContexts relation is provided then there "\
                            "shall be no instance of IfcGeometricRepresentationSubContext "\
                            "directly included in the set of RepresentationContexts"


    def CorrectEventTriggerType(self, entity, ifcname, called_entity=None):
        """Checks if the user defined event trigger type attribute is asserted, when the event
        trigger type is set to userdefined.
        ----------
        This is used in IfcEventType."""
        if entity.attrib["EventTriggerType"].lower() == "userdefined":
            if (
                "UserDefinedEventTriggerType" not in entity.attrib
                or entity.attrib["UserDefinedEventTriggerType"] == ""
            ):
                return "The attribute UserDefinedEventTriggerType must be asserted when the "\
                    "value of EventTriggerType is set to USERDEFINED"


    def CorrectItemsForType(self, entity, ifcname, called_entity=None):
        """Checks if the items are properly used.
        ----------
        This is used in IfcShapeRepresentation."""
        rep_type = entity.attrib["RepresentationType"]
        items = entity.find("Items")
        result = self.IfcShapeRepresentationTypes(rep_type, items)
        if not result:
            return "According to the RepresentationType the Items aren't properly used"
        elif result == "?":
            return "Not possible to check the proper use of Items according to the "\
                "RepresentationType, since the RespresentationType is unknown"


    def CorrectPhysOrVirt(self, entity, ifcname, called_entity=None):
        """Checks if the space boundary and its associated elements are either physical or virtual.
        ----------
        This is used in IfcRelSpaceBoundary."""
        boundary = entity.attrib["PhysicalOrVirtualBoundary"].lower()
        bldg_element = (
            entity.parent().parent()
            if called_entity == "RelatedBuildingElement"
            else entity.find("RelatedBuildingElement")
        )
        if bldg_element is None:
            identifier = entity.attrib["id"]
            referenced = self.tree.findall(f".//*[@ref='{identifier}']")
            if len(referenced) > 0:
                for ref in referenced:
                    if ref.getparent().tag == "ProvidesBoundaries":
                        bldg_element = ref.getparent().getparent()
                        break
        if "ref" in bldg_element.attrib:
            bldg_element = self.ref_check(bldg_element)
        bldg_element = (
            bldg_element.attrib[self.type] if self.type in bldg_element.attrib else bldg_element.tag
        )
        if boundary == "physical":
            if self.attr_check(bldg_element, "IfcVirtualElement"):
                test1 = False
            else:
                test1 = True

        elif boundary == "virtual":
            allowed = ["IfcVirtualElement", "IfcOpeningElement"]
            test2 = self.attr_list_check(bldg_element, allowed)

        test3 = bool(boundary == "notdefined")

        if not (test1 or test2 or test3):
            return "If the space boundary is physical, it shall be provided by an element "\
                "(i.e. excluding a virtual element). If the space boundary is virtual, it shall "\
                "either have a virtual element or an opening providing the space boundary. If the "\
                "space boundary PhysicalOrVirtualBoundary attribute is not defined, no "\
                "restrictions are imposed"


    def CorrectPredefinedType(self, entity, ifcname, called_entity=None):
        """Checks if an object (or process or element) type is given, if the predefined type is
        set to userdefined.
        ----------
        This is used in IfcBuildingElementProxy, IfcBuildingElementProxyType, IfcEvent,
        IfcEventType, IfcProcedure, IfcProcedureType, IfcTask, IfcTaskType, IfcWorkCalendar,
        IfcWorkPlan, IfcWorkSchedule, IfcElementAssembly, IfcElementAssemblyType,
        IfcGeographicElement, IfcGeographicElementType, IfcSpace, IfcSpaceType, IfcSpatialZone,
        IfcSpatialZoneType, IfcTransportElement, IfcTransportElementType, IfcBeam, IfcBeamType,
        IfcChimney, IfcChimneyType, IfcColumn, IfcColumnType, IfcCovering, IfcCoveringType,
        IfcCurtainWall, IfcCurtainWallType, DoorType, IfcMember, IfcMemberType, IfcPlate,
        IfcPlateType, IfcRailing, IfcRailingType, IfcRamp, IfcRampType, IfcRampFlight,
        IfcRampFlightType, IfcRoof, IfcRoofType, IfcShadingDevice, IfcShadingDeviceType, IfcSlab,
        IfcSlabType, IfcStair, IfcStairType, IfcStairFlight, IfcStairFlightType, IfcWall,
        IfcWallType, IfcWindowType, IfcBuildingElementPart, IfcBuildingElementPartType,
        IfcDiscreteAccessory, IfcDiscreteAccessoryType, IfcFastener, IfcFastenerType,
        IfcMechanicalFastener, IfcMechanicalFastenerType, IfcActuator, IfcAlarm, IfcController,
        IfcFlowInstrument, IfcSensor, IfcUnitaryControlElement, IfcAudioVisualAppliance,
        IfcCableCarrierFitting, IfcCableCarrierSegment, IfcCableFitting, IfcCableSegment,
        IfcCommunicationsAppliance, IfcElectricAppliance, IfcElectricDistributionBoard,
        IfcElectricFlowStorageDevice, IfcElectricGenerator, IfcElectricMotor,
        IfcElectricTimeControl, IfcJunctionBox, IfcLamp, IfcLightFixture, IfcMotorConnection,
        IfcOutlet, IfcProtectiveDevice, IfcProtectiveDeviceTrippingUnit, IfcSolarDevice,
        IfcSwitchingDevice, IfcTransformer, IfcAirTerminal, IfcAirTerminalBox,
        IfcAirToAirHeatRecovery, IfcBoiler, IfcBurner, IfcChiller, IfcCoil, IfcCompressor,
        IfcCondenser, IfcCooledBeam, IfcCoolingTower, IfcDamper, IfcDuctFitting, IfcDuctSegment,
        IfcDuctSilencer, IfcEngine, IfcEvaporativeCooler, IfcEvaporator, IfcFan, IfcFilter,
        IfcFlowMeter, IfcHeatExchanger, IfcHumidifier, IfcMedicalDevice, IfcPipeFitting,
        IfcPipeSegment, IfcPump, IfcSpaceHeater, IfcTank, IfcTubeBundle, IfcUnitaryEquipment,
        IfcValve, IfcVibrationIsolator, IfcFireSuppressionTerminal, IfcInterceptor,
        IfcSanitaryTerminal, IfcStackTerminal, IfcWasteTerminal, IfcFooting, IfcFootingType,
        IfcPile, IfcPileType, IfcReinforcingBar, IfcReinforcingBarType, IfcReinforcingMesh,
        IfcReinforcingMeshType, IfcTendon, IfcTendonType, IfcTendonAnchor, IfcTendonAnchorType,
        IfcActuatorType, IfcAlarmType, IfcControllerType, IfcFlowInstrumentType, IfcSensorType,
        IfcUnitaryControlElementType, IfcAudioVisualApplianceType, IfcCableCarrierFittingType,
        IfcCableCarrierSegmentType, IfcCableFittingType, IfcCableSegmentType,
        IfcCommunicationsApplianceType, IfcElectricApplianceType, IfcElectricDistributionBoardType,
        IfcElectricFlowStorageDeviceType, IfcElectricGeneratorType, IfcElectricMotorType,
        IfcElectricTimeControlType, IfcJunctionBoxType, IfcLampType, IfcLightFixtureType,
        IfcMotorConnectionType, IfcOutletType, IfcProtectiveDeviceType,
        IfcProtectiveDeviceTrippingUnitType, IfcSolarDeviceType, IfcSwitchingDeviceType,
        IfcTransformerType, IfcAirTerminalType, IfcAirTerminalBoxType, IfcAirToAirHeatRecoveryType,
        IfcBoilerType, IfcBurnerType, IfcChillerType, IfcCoilType, IfcCompressorType,
        IfcCondenserType, IfcCooledBeamType, IfcCoolingTowerType, IfcDamperType,
        IfcDuctFittingType, IfcDuctSegmentType, IfcDuctSilencerType, IfcEngineType,
        IfcEvaporativeCoolerType, IfcEvaporatorType, IfcFanType, IfcFilterType, IfcFlowMeterType,
        IfcHeatExchangerType, IfcHumidifierType, IfcMedicalDeviceType, IfcPipeFittingType,
        IfcPipeSegmentType, IfcPumpType, IfcSpaceHeaterType, IfcTankType, IfcTubeBundleType,
        IfcUnitaryEquipmentType, IfcValveType, IfcVibrationIsolatorType,
        IfcFireSuppressionTerminalType, IfcInterceptorType, IfcSanitaryTerminalType,
        IfcStackTerminalType & IfcWasteTerminalType."""
        object_types = [
            "IfcBuildingElementProxy",
            "IfcEvent",
            "IfcProcedure",
            "IfcTask",
            "IfcWorkCalendar",
            "IfcWorkPlan",
            "IfcWorkSchedule",
            "IfcElementAssembly",
            "IfcGeographicElement",
            "IfcSpace",
            "IfcSpatialZone",
            "IfcTransportElement",
            "IfcBeam",
            "IfcChimney",
            "IfcColumn",
            "IfcCovering",
            "IfcCurtainWall",
            "IfcMember",
            "IfcPlate",
            "IfcRailing",
            "IfcRamp",
            "IfcRampFlight",
            "IfcRoof",
            "IfcShadingDevice",
            "IfcSlab",
            "IfcStair",
            "IfcStairFlight",
            "IfcWall",
            "IfcBuildingElementPart",
            "IfcDiscreteAccessory",
            "IfcFastener",
            "IfcMechanicalFastener",
            "IfcActuator",
            "IfcAlarm",
            "IfcController",
            "IfcFlowInstrument",
            "IfcSensor",
            "IfcUnitaryControlElement",
            "IfcAudioVisualAppliance",
            "IfcCableCarrierFitting",
            "IfcCableCarrierSegment",
            "IfcCableFitting",
            "IfcCableSegment",
            "IfcCommunicationsAppliance",
            "IfcElectricAppliance",
            "IfcElectricDistributionBoard",
            "IfcElectricFlowStorageDevice",
            "IfcElectricGenerator",
            "IfcElectricMotor",
            "IfcElectricTimeControl",
            "IfcJunctionBox",
            "IfcLamp",
            "IfcLightFixture",
            "IfcMotorConnection",
            "IfcOutlet",
            "IfcProtectiveDevice",
            "IfcProtectiveDeviceTrippingUnit",
            "IfcSolarDevice",
            "IfcSwitchingDevice",
            "IfcTransformer",
            "IfcAirTerminal",
            "IfcAirTerminalBox",
            "IfcAirToAirHeatRecovery",
            "IfcBoiler",
            "IfcBurner",
            "IfcChiller",
            "IfcCoil",
            "IfcCompressor",
            "IfcCondenser",
            "IfcCooledBeam",
            "IfcCoolingTower",
            "IfcDamper",
            "IfcDuctFitting",
            "IfcDuctSegment",
            "IfcDuctSilencer",
            "IfcEngine",
            "IfcEvaporativeCooler",
            "IfcEvaporator",
            "IfcFan",
            "IfcFilter",
            "IfcFlowMeter",
            "IfcHeatExchanger",
            "IfcHumidifier",
            "IfcMedicalDevice",
            "IfcPipeFitting",
            "IfcPipeSegment",
            "IfcPump",
            "IfcSpaceHeater",
            "IfcTank",
            "IfcTubeBundle",
            "IfcUnitaryEquipment",
            "IfcValve",
            "IfcVibrationIsolator",
            "IfcFireSuppressionTerminal",
            "IfcInterceptor",
            "IfcSanitaryTerminal",
            "IfcStackTerminal",
            "IfcWasteTerminal",
            "IfcFooting",
            "IfcPile",
            "IfcReinforcingBar",
            "IfcReinforcingMesh",
            "IfcTendon",
            "IfcTendonAnchor",
        ]
        process_types = ["IfcEventType", "IfcProcedureType", "IfcTaskType"]
        element_types = [
            "IfcBuildingElementProxyType",
            "IfcElementAssemblyType",
            "IfcGeographicElementType",
            "IfcSpaceType",
            "IfcSpatialZoneType",
            "IfcTransportElementType",
            "IfcBeamType",
            "IfcChimneyType",
            "IfcColumnType",
            "IfcCoveringType",
            "IfcCurtainWallType",
            "IfcDoorType",
            "IfcMemberType",
            "IfcPlateType",
            "IfcRailingType",
            "IfcRampType",
            "IfcRampFlightType",
            "IfcRoofType",
            "IfcShadingDeviceType",
            "IfcSlabType",
            "IfcStairType",
            "IfcStairFlightType",
            "IfcWallType",
            "IfcWindowType",
            "IfcBuildingElementPartType",
            "IfcDiscreteAccessoryType",
            "IfcFastenerType",
            "IfcMechanicalFastenerType",
            "IfcActuatorType",
            "IfcAlarmType",
            "IfcControllerType",
            "IfcFlowInstrumentType",
            "IfcSensorType",
            "IfcUnitaryControlElementType",
            "IfcAudioVisualApplianceType",
            "IfcCableCarrierFittingType",
            "IfcCableCarrierSegmentType",
            "IfcCableFittingType",
            "IfcCableSegmentType",
            "IfcCommunicationsApplianceType",
            "IfcElectricApplianceType",
            "IfcElectricDistributionBoardType",
            "IfcElectricFlowStorageDeviceType",
            "IfcElectricGeneratorType",
            "IfcElectricMotorType",
            "IfcElectricTimeControlType",
            "IfcJunctionBoxType",
            "IfcLampType",
            "IfcLightFixtureType",
            "IfcMotorConnectionType",
            "IfcOutletType",
            "IfcProtectiveDeviceType",
            "IfcProtectiveDeviceTrippingUnitType",
            "IfcSolarDeviceType",
            "IfcSwitchingDeviceType",
            "IfcTransformerType",
            "IfcAirTerminalType",
            "IfcAirTerminalBoxType",
            "IfcAirToAirHeatRecoveryType",
            "IfcBoilerType",
            "IfcBurnerType",
            "IfcChillerType",
            "IfcCoilType",
            "IfcCompressorType",
            "IfcCondenserType",
            "IfcCooledBeamType",
            "IfcCoolingTowerType",
            "IfcDamperType",
            "IfcDuctFittingType",
            "IfcDuctSegmentType",
            "IfcDuctSilencerType",
            "IfcEngineType",
            "IfcEvaporativeCoolerType",
            "IfcEvaporatorType",
            "IfcFanType",
            "IfcFilterType",
            "IfcFlowMeterType",
            "IfcHeatExchangerType",
            "IfcHumidifierType",
            "IfcMedicalDeviceType",
            "IfcPipeFittingType",
            "IfcPipeSegmentType",
            "IfcPumpType",
            "IfcSpaceHeaterType",
            "IfcTankType",
            "IfcTubeBundleType",
            "IfcUnitaryEquipmentType",
            "IfcValveType",
            "IfcVibrationIsolatorType",
            "IfcFireSuppressionTerminalType",
            "IfcInterceptorType",
            "IfcSanitaryTerminalType",
            "IfcStackTerminalType",
            "IfcWasteTerminalType",
            "IfcFootingType",
            "IfcPileType",
            "IfcReinforcingBarType",
            "IfcReinforcingMeshType",
            "IfcTendonType",
            "IfcTendonAnchorType",
        ]
        if ifcname in object_types:
            if "PredefinedType" in entity.attrib:
                if entity.attrib["PredefinedType"].lower() == "userdefined":
                    if "ObjectType" not in entity.attrib or entity.attrib["ObjectType"] == "":
                        return "Either the PredefinedType attribute is unset, or the inherited "\
                            "attribute ObjectType shall be provided, if the PredefinedType is "\
                            "set to USERDEFINED"
        elif ifcname in process_types:
            if entity.attrib["PredefinedType"].lower() == "userdefined":
                if "ProcessType" not in entity.attrib or entity.attrib["ProcessType"] == "":
                    return "The attribute ProcessType must be asserted when the value of "\
                        "PredefinedType is set to USERDEFINED"
        elif ifcname in element_types:
            if entity.attrib["PredefinedType"].lower() == "userdefined":
                if "ElementType" not in entity.attrib or entity.attrib["ElementType"] == "":
                    return "The inherited attribute ElementType shall be provided, if the "\
                        "PredefinedType is set to USERDEFINED"


    def CorrectProfileAssignment(self, entity, ifcname, called_entity=None):
        """Checks if the start and end profile are compatible.
        ----------
        This is used in IfcExtrudedAreaSolidTapered & IfcRevolvedAreaSolidTapered."""
        start = entity.find("SweptArea")
        if "ref" in start.attrib:
            start = self.ref_check(start)
        end = entity.find("EndSweptArea")
        if "ref" in end.attrib:
            end = self.ref_check(end)
        result = self.IfcTaperedSweptAreaProfiles(start, end)
        if not result:
            return "The SweptArea as start profile and the EndSweptArea as end profile shall "\
                "be compatible"


    def CorrectRadii(self, entity, ifcname, called_entity=None):
        """Checks if the fillet radius is greater than the inner radius.
        ----------
        This is used in IfcSweptDiskSolidPolygonal."""
        if "FilletRadius" in entity.attrib:
            if float(entity.attrib["FilletRadius"]) < float(entity.attrib["InnerRadius"]):
                return "If a FilletRadius is given, it has to be greater or equal to the Radius "\
                    "of the disk"


    def CorrectSequenceType(self, entity, ifcname, called_entity=None):
        """Checks if a user defined sequence type is given, if the type is set to userdefined.
        ----------
        This is used in IfcRelSequence."""
        if "SequenceType" in entity.attrib:
            if entity.attrib["SequenceType"].lower() == "userdefined":
                if (
                    "UserDefinedSequenceType" not in entity.attrib
                    or entity.attrib["UserDefinedSequenceType"] == ""
                ):
                    return "The attribute UserDefinedSequenceType must be asserted when the "\
                        "value of SequenceType is set to USERDEFINED"


    def CorrectStyleAssigned(self, entity, ifcname, called_entity=None):
        """Checks if the correct style is assigned.
        ----------
        This is used in IfcDoor & IfcWindow."""
        if ifcname == "IfcDoor":
            if entity.find("IsTypedBy") is not None:
                rel_object = entity.find("IsTypedBy")
                if "ref" in rel_object.attrib:
                    rel_object = self.ref_check(rel_object)
                rel_type = rel_object.find("RelatingType")
                if "ref" in rel_type.attrib:
                    rel_type = self.ref_check(rel_type)
                rel_type = (
                    rel_type.attrib[self.type] if self.type in rel_type.attrib else rel_type.tag
                )
                if not self.attr_check(rel_type, "IfcDoorType"):
                    return "Either there is no door type object associated, i.e. the IsTypedBy "\
                        "inverse relationship is not provided, or the associated type object has "\
                        "to be of type IfcDoorType"
        elif ifcname == "IfcWindow":
            if entity.find("IsTypedBy") is not None:
                rel_object = entity.find("IsTypedBy")
                if "ref" in rel_object.attrib:
                    rel_object = self.ref_check(rel_object)
                rel_type = rel_object.find("RelatingType")
                if "ref" in rel_type.attrib:
                    rel_type = self.ref_check(rel_type)
                rel_type = (
                    rel_type.attrib[self.type] if self.type in rel_type.attrib else rel_type.tag
                )
                if not self.attr_check(rel_type, "IfcWindowType"):
                    return "Either there is no window type object associated, i.e. the IsTypedBy "\
                        "inverse relationship is not provided, or the associated type object has "\
                        "to be of type IfcWindowType"


    def CorrectTypeAssigned(self, entity, ifcname, called_entity=None):
        """Checks if the correct type is assigned.
        ----------
        This is used in IfcBuildingElementProxy, IfcEvent, IfcElementAssembly,
        IfcGeographicElement, IfcSpace, IfcSpatialZone, IfcTransportElement, IfcBeam, IfcChimney,
        IfcColumn, IfcCovering, IfcCurtainWall, IfcMember, IfcPlate, IfcRailing, IfcRamp,
        IfcRampFlight, IfcRoof, IfcShadingDevice, IfcSlab, IfcStair, IfcStairFlight, IfcWall,
        IfcBuildingElementPart, IfcDiscreteAccessory, IfcFastener, IfcMechanicalFastener,
        IfcActuator, IfcAlarm, IfcController, IfcFlowInstrument, IfcSensor,
        IfcUnitaryControlElement, IfcAudioVisualAppliance, IfcCableCarrierFitting,
        IfcCableCarrierSegment, IfcCableFitting, IfcCableSegment, IfcCommunicationsAppliance,
        IfcElectricAppliance, IfcElectricDistributionBoard, IfcElectricFlowStorageDevice,
        IfcElectricGenerator, IfcElectricMotor, IfcElectricTimeControl, IfcJunctionBox, IfcLamp,
        IfcLightFixture, IfcMotorConnection, IfcOutlet, IfcProtectiveDevice,
        IfcProtectiveDeviceTrippingUnit, IfcSolarDevice, IfcSwitchingDevice, IfcTransformer,
        IfcAirTerminal, IfcAirTerminalBox, IfcAirToAirHeatRecovery, IfcBoiler, IfcBurner,
        IfcChiller, IfcCoil, IfcCompressor, IfcCondenser, IfcCooledBeam, IfcCoolingTower,
        IfcDamper, IfcDuctFitting, IfcDuctSegment, IfcDuctSilencer, IfcEngine,
        IfcEvaporativeCooler, IfcEvaporator, IfcFan, IfcFilter, IfcFlowMeter, IfcHeatExchanger,
        IfcHumidifier, IfcMedicalDevice, IfcPipeFitting, IfcPipeSegment, IfcPump, IfcSpaceHeater,
        IfcTank, IfcTubeBundle, IfcUnitaryEquipment, IfcValve, IfcVibrationIsolator,
        IfcFireSuppressionTerminal, IfcInterceptor, IfcSanitaryTerminal, IfcStackTerminal,
        IfcWasteTerminal, IfcFooting, IfcPile, IfcReinforcingBar, IfcReinforcingMesh, IfcTendon,
        IfcTendonAnchor."""
        if ifcname == "IfcEvent":
            if "EventTriggerType" in entity.attrib:
                if entity.attrib["EventTriggerType"].lower() == "userdefined":
                    if (
                        "UserDefinedEventTriggerType" not in entity.attrib
                        or entity.attrib["UserDefinedEventTriggerType"] == ""
                    ):
                        return "Either the EventTriggerType attribute is unset, or the attribute "\
                            "UserDefinedEventTriggerType must be asserted when the value of "\
                            "EventTriggerType is set to USERDEFINED"
        else:
            if ifcname == "IfcBuildingElementProxy":
                ifctype = "IfcBuildingElementProxyType"
            elif ifcname == "IfcElementAssembly":
                ifctype = "IfcElementAssemblyType"
            elif ifcname == "IfcGeographicElement":
                ifctype = "IfcGeographicElementType"
            elif ifcname == "IfcSpace":
                ifctype = "IfcSpaceType"
            elif ifcname == "IfcSpatialZone":
                ifctype = "IfcSpatialZoneType"
            elif ifcname == "IfcTransportElement":
                ifctype = "IfcTransportElementType"
            elif ifcname == "IfcBeam":
                ifctype = "IfcBeamType"
            elif ifcname == "IfcChimney":
                ifctype = "IfcChimneyType"
            elif ifcname == "IfcColumn":
                ifctype = "IfcColumnType"
            elif ifcname == "IfcCovering":
                ifctype = "IfcCoveringType"
            elif ifcname == "IfcCurtainWall":
                ifctype = "IfcCurtainWallType"
            elif ifcname == "IfcMember":
                ifctype = "IfcMemberType"
            elif ifcname == "IfcPlate":
                ifctype = "IfcPlateType"
            elif ifcname == "IfcRailing":
                ifctype = "IfcRailingType"
            elif ifcname == "IfcRamp":
                ifctype = "IfcRampType"
            elif ifcname == "IfcRampFlight":
                ifctype = "IfcRampFlightType"
            elif ifcname == "IfcRoof":
                ifctype = "IfcRoofType"
            elif ifcname == "IfcShadingDevice":
                ifctype = "IfcShadingDeviceType"
            elif ifcname == "IfcSlab":
                ifctype = "IfcSlabType"
            elif ifcname == "IfcStair":
                ifctype = "IfcStairType"
            elif ifcname == "IfcStairFlight":
                ifctype = "IfcStairFlightType"
            elif ifcname == "IfcWall":
                ifctype = "IfcWallType"
            elif ifcname == "IfcBuildingElementPart":
                ifctype = "IfcBuildingElementPartType"
            elif ifcname == "IfcDiscreteAccessory":
                ifctype = "IfcDiscreteAccessoryType"
            elif ifcname == "IfcFastener":
                ifctype = "IfcFastenerType"
            elif ifcname == "IfcMechanicalFastener":
                ifctype = "IfcMechanicalFastenerType"
            elif ifcname == "IfcActuator":
                ifctype = "IfcActuatorType"
            elif ifcname == "IfcAlarm":
                ifctype = "IfcAlarmType"
            elif ifcname == "IfcController":
                ifctype = "IfcControllerType"
            elif ifcname == "IfcFlowInstrument":
                ifctype = "IfcFlowInstrumentType"
            elif ifcname == "IfcSensor":
                ifctype = "IfcSensorType"
            elif ifcname == "IfcUnitaryControlElement":
                ifctype = "IfcUnitaryControlElementType"
            elif ifcname == "IfcAudioVisualAppliance":
                ifctype = "IfcAudioVisualApplianceType"
            elif ifcname == "IfcCableCarrierFitting":
                ifctype = "IfcCableCarrierFittingType"
            elif ifcname == "IfcCableCarrierSegment":
                ifctype = "IfcCableCarrierSegmentType"
            elif ifcname == "IfcCableFitting":
                ifctype = "IfcCableFittingType"
            elif ifcname == "IfcCableSegment":
                ifctype = "IfcCableSegmentType"
            elif ifcname == "IfcCommunicationsAppliance":
                ifctype = "IfcCommunicationsApplianceType"
            elif ifcname == "IfcElectricAppliance":
                ifctype = "IfcElectricApplianceType"
            elif ifcname == "IfcElectricDistributionBoard":
                ifctype = "IfcElectricDistributionBoardType"
            elif ifcname == "IfcElectricFlowStorageDevice":
                ifctype = "IfcElectricFlowStorageDeviceType"
            elif ifcname == "IfcElectricGenerator":
                ifctype = "IfcElectricGeneratorType"
            elif ifcname == "IfcElectricMotor":
                ifctype = "IfcElectricMotorType"
            elif ifcname == "IfcElectricTimeControl":
                ifctype = "IfcElectricTimeControlType"
            elif ifcname == "IfcJunctionBox":
                ifctype = "IfcJunctionBoxType"
            elif ifcname == "IfcLamp":
                ifctype = "IfcLampType"
            elif ifcname == "IfcLightFixture":
                ifctype = "IfcLightFixtureType"
            elif ifcname == "IfcMotorConnection":
                ifctype = "IfcMotorConnectionType"
            elif ifcname == "IfcOutlet":
                ifctype = "IfcOutletType"
            elif ifcname == "IfcProtectiveDevice":
                ifctype = "IfcProtectiveDeviceType"
            elif ifcname == "IfcProtectiveDeviceTrippingUnit":
                ifctype = "IfcProtectiveDeviceTrippingUnitType"
            elif ifcname == "IfcSolarDevice":
                ifctype = "IfcSolarDeviceType"
            elif ifcname == "IfcSwitchingDevice":
                ifctype = "IfcSwitchingDeviceType"
            elif ifcname == "IfcTransformer":
                ifctype = "IfcTransformerType"
            elif ifcname == "IfcAirTerminal":
                ifctype = "IfcAirTerminalType"
            elif ifcname == "IfcAirTerminalBox":
                ifctype = "IfcAirTerminalBoxType"
            elif ifcname == "IfcAirToAirHeatRecovery":
                ifctype = "IfcAirToAirHeatRecoveryType"
            elif ifcname == "IfcBoiler":
                ifctype = "IfcBoilerType"
            elif ifcname == "IfcBurner":
                ifctype = "IfcBurnerType"
            elif ifcname == "IfcChiller":
                ifctype = "IfcChillerType"
            elif ifcname == "IfcCoil":
                ifctype = "IfcCoilType"
            elif ifcname == "IfcCompressor":
                ifctype = "IfcCompressorType"
            elif ifcname == "IfcCondenser":
                ifctype = "IfcCondenserType"
            elif ifcname == "IfcCooledBeam":
                ifctype = "IfcCooledBeamType"
            elif ifcname == "IfcCoolingTower":
                ifctype = "IfcCoolingTowerType"
            elif ifcname == "IfcDamper":
                ifctype = "IfcDamperType"
            elif ifcname == "IfcDuctFitting":
                ifctype = "IfcDuctFittingType"
            elif ifcname == "IfcDuctSegment":
                ifctype = "IfcDuctSegmentType"
            elif ifcname == "IfcDuctSilencer":
                ifctype = "IfcDuctSilencerType"
            elif ifcname == "IfcEngine":
                ifctype = "IfcEngineType"
            elif ifcname == "IfcEvaporativeCooler":
                ifctype = "IfcEvaporativeCoolerType"
            elif ifcname == "IfcEvaporator":
                ifctype = "IfcEvaporatorType"
            elif ifcname == "IfcFan":
                ifctype = "IfcFanType"
            elif ifcname == "IfcFilter":
                ifctype = "IfcFilterType"
            elif ifcname == "IfcFlowMeter":
                ifctype = "IfcFlowMeterType"
            elif ifcname == "IfcHeatExchanger":
                ifctype = "IfcHeatExchangerType"
            elif ifcname == "IfcHumidifier":
                ifctype = "IfcHumidifierType"
            elif ifcname == "IfcMedicalDevice":
                ifctype = "IfcMedicalDeviceType"
            elif ifcname == "IfcPipeFitting":
                ifctype = "IfcPipeFittingType"
            elif ifcname == "IfcPipeSegment":
                ifctype = "IfcPipeSegmentType"
            elif ifcname == "IfcPump":
                ifctype = "IfcPumpType"
            elif ifcname == "IfcSpaceHeater":
                ifctype = "IfcSpaceHeaterType"
            elif ifcname == "IfcTank":
                ifctype = "IfcTankType"
            elif ifcname == "IfcTubeBundle":
                ifctype = "IfcTubeBundleType"
            elif ifcname == "IfcUnitaryEquipment":
                ifctype = "IfcUnitaryEquipmentType"
            elif ifcname == "IfcValve":
                ifctype = "IfcValveType"
            elif ifcname == "IfcVibrationIsolator":
                ifctype = "IfcVibrationIsolatorType"
            elif ifcname == "IfcFireSuppressionTerminal":
                ifctype = "IfcFireSuppressionTerminalType"
            elif ifcname == "IfcInterceptor":
                ifctype = "IfcInterceptorType"
            elif ifcname == "IfcSanitaryTerminal":
                ifctype = "IfcSanitaryTerminalType"
            elif ifcname == "IfcStackTerminal":
                ifctype = "IfcStackTerminalType"
            elif ifcname == "IfcWasteTerminal":
                ifctype = "IfcWasteTerminalType"
            elif ifcname == "IfcFooting":
                ifctype = "IfcFootingType"
            elif ifcname == "IfcPile":
                ifctype = "IfcPileType"
            elif ifcname == "IfcReinforcingBar":
                ifctype = "IfcReinforcingBarType"
            elif ifcname == "IfcReinforcingMesh":
                ifctype = "IfcReinforcingMeshType"
            elif ifcname == "IfcTendon":
                ifctype = "IfcTendonType"
            elif ifcname == "IfcTendonAnchor":
                ifctype = "IfcTendonAnchorType"
            else:
                #Type not found.
                pass

            if entity.find("IsTypedBy") is not None:
                rel_object = entity.find("IsTypedBy")
                if "ref" in rel_object.attrib:
                    rel_object = self.ref_check(rel_object)
                rel_type = rel_object.find("RelatingType")
                if "ref" in rel_type.attrib:
                    rel_type = self.ref_check(rel_type)
                rel_type = (
                    rel_type.attrib[self.type] if self.type in rel_type.attrib else rel_type.tag
                )
                if not self.attr_check(rel_type, ifctype):
                    return (
                        "Either there is no transport element type object associated, i.e. the "
                        + "IsTypedBy inverse relationship is not provided, or the associated "
                        + "type object has to be of type " + ifctype
                    )


    def CorrespondingKnotLists(self, entity, ifcname, called_entity=None):
        """Checks if the number of elements in knot multiplicities an knots list is consistent.
        ----------
        This is used in IfcBSplineCurveWithKnots."""
        km = len(re.split(r"\s+", str(entity.attrib["KnotMultiplicities"])))
        knots = len(re.split(r"\s+", str(entity.attrib["Knots"])))
        if km != knots:
            return "The number of elements in the knot multiplicities list shall be equal to the "\
                "number of elements in the knots list"


    def CorrespondingSectionPositions(self, entity, ifcname, called_entity=None):
        """Checks if the number of cross sections and cross section positions is equal.
        ----------
        This is used in IfcSectionedSpine."""
        sections = len(re.split(r"\s+", str(entity.attrib["CrossSections"])))
        positions = len(re.split(r"\s+", str(entity.attrib["CrossSectionPositions"])))
        if sections != positions:
            return "The set of cross sections and the set of cross section positions shall be of "\
                "the same size"


    def CorrespondingULists(self, entity, ifcname, called_entity=None):
        """Checks if the number of u-multiplicities is equal to the number of u-knots.
        ----------
        This is used in IfcBSplineSurfaceWithKnots."""
        multi = len(re.split(r"\s+", str(entity.attrib["UMultiplicities"])))
        knots = len(re.split(r"\s+", str(entity.attrib["UKnots"])))
        if multi != knots:
            return "The number of UMultiplicities shall be the same as the number of UKnots"


    def CorrespondingVLists(self, entity, ifcname, called_entity=None):
        """Checks if the number of v-multiplicities is equal to the number of v-knots.
        ----------
        This is used in IfcBSplineSurfaceWithKnots."""
        multi = len(re.split(r"\s+", str(entity.attrib["VMultiplicities"])))
        knots = len(re.split(r"\s+", str(entity.attrib["VKnots"])))
        if multi != knots:
            return "The number of VMultiplicities shall be the same as the number of VKnots"


    def CorrespondingWeightsDataLists(self, entity, ifcname, called_entity=None):
        """Checks if the dimension for the weights is the same for each control point.
        ----------
        This is used in IfcRationalBSplineSurfaceWithKnots."""
        cpl = len(re.split(r"\s+", str(entity.attrib["ControlPointsList"])))
        weights = len(re.split(r"\s+", str(entity.attrib["WeightsData"])))
        if cpl != weights:
            return "The array dimensions for the weights shall be consistent with the control "\
                "points data"


    def CurveContinuous(self, entity, ifcname, called_entity=None):
        """Checks if the curve is continuous except for the last segment in case of an open curve.
        ----------
        This is used in IfcCompositeCurve."""
        if called_entity == "Segments":
            segments = []
            segments.append(entity.getparent().getparent())
        else:
            segments = entity.find("Segments")
            if segments is None:
                segments = []
                identifier = entity.attrib["id"]
                referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                if len(referenced) > 0:
                    for ref in referenced:
                        if ref.getparent().tag == "UsingCurve":
                            segments.append(ref.getparent().getparent())
        for i in range(len(segments) - 1):
            if "ref" in segments[i].attrib:
                segments[i] = self.ref_check(segments[i])
            if segments[i].attrib["Transition"].lower() == "discontinuous":
                return "No transition code should be Discontinuous, except for the last code of "\
                    "an open curve"


    def CurveIs3D(self, entity, ifcname, called_entity=None):
        """Checks if the curve is 3D.
        ----------
        This is used in IfcSurfaceCurve."""
        curve = entity.find("Curve3D")
        if "ref" in curve.attrib:
            curve = self.ref_check(curve)
        ifccurve = curve.attrib[self.type] if self.type in curve.attrib else curve.tag
        dimension = self.IfcDimensionSize(curve, ifccurve)
        if dimension != 3:
            return "Dimension has to be 3D"


    def CurveIsNotPcurve(self, entity, ifcname, called_entity=None):
        """Checks if the 3D curve is not a Pcurve.
        ----------
        This is used in IfcSurfaceCurve."""
        curve = entity.find("Curve3D")
        if "ref" in curve.attrib:
            curve = self.ref_check(curve)
        curve_type = curve.attrib[self.type] if self.type in curve.attrib else curve.tag
        if curve_type == "IfcPcurve":
            return "Curve3D must not be a Pcurve"


    def DimEqual2(self, entity, ifcname, called_entity=None):
        """Checks if the entity is 2D.
        ----------
        This is used in IfcCartesianTransformationOperator2D."""
        origin = entity.find("LocalOrigin")
        if "ref" in origin.attrib:
            origin = self.ref_check(origin)
        if len(re.split(r"\s+", origin.attrib["Coordinates"])) != 2:
            return "Dimension has to be 2D"


    def DimIs2D(self, entity, ifcname, called_entity=None):
        """Checks if the entity is 2D.
        ----------
        This is used in IfcOffsetCurve2D & IfcPcurve."""
        if ifcname == "IfcPcurve":
            curve = entity.find("ReferenceCurve")
            if "ref" in curve.attrib:
                curve = self.ref_check(curve)
        else:
            curve = entity.find("BasisCurve")
            if "ref" in curve.attrib:
                curve = self.ref_check(curve)

        ifccurve = curve.attrib[self.type] if self.type in curve.attrib else curve.tag
        dimension = self.IfcDimensionSize(curve, ifccurve)
        if dimension != 2:
            return "Dimension has to be 2D"


    def DimIs3D(self, entity, ifcname, called_entity=None):
        """Checks if the entity is 3D.
        ----------
        This is used in IfcCartesianTransformationOperator3D & IfcOffsetCurve3D."""
        if ifcname == "IfcCartesianTransformationOperator3D":
            origin = entity.find("LocalOrigin")
            if "ref" in origin.attrib:
                origin = self.ref_check(origin)
            if len(re.split(r"\s+", origin.attrib["Coordinates"])) != 3:
                return "Dimension has to be 3D"
        else:
            curve = entity.find("BasisCurve")
            if "ref" in curve.attrib:
                curve = self.ref_check(curve)
            ifccurve = curve.attrib[self.type] if self.type in curve.attrib else curve.tag
            dimension = self.IfcDimensionSize(curve, ifccurve)
            if dimension != 3:
                return "Dimension has to be 3D"


    def DirectrixBounded(self, entity, ifcname, called_entity=None):
        """Checks if the directrix is bounded or a closed curve, if no start and/or end parameter
        are specified.
        ----------
        This is used in IfcFixedReferenceSweptAreaSolid, IfcSurfaceCurveSweptAreaSolid
        & IfcSweptDiskSolid."""
        if ("StartParam" not in entity.attrib or entity.attrib["StartParam"] == "") or (
            "EndParam" not in entity.attrib or entity.attrib["EndParam"] == ""
        ):
            allowed_directrix = ["IfcConic", "IfcBoundedCurve"]
            directrix = entity.find("Directrix")
            if "ref" in directrix.attrib:
                directrix = self.ref_check(directrix)
            directrix = (
                directrix.attrib[self.type] if self.type in directrix.attrib else directrix.tag
            )
            if not self.attr_list_check(directrix, allowed_directrix):
                return "If the values for StartParam or EndParam are omited, then the Directrix "\
                    "has to be a bounded or closed curve"


    def DirectrixDim(self, entity, ifcname, called_entity=None):
        """Checks if the directrix is 3D.
        ----------
        This is used in IfcSweptDiskSolid."""
        directrix = entity.find("Directrix")
        if "ref" in directrix.attrib:
            directrix = self.ref_check(directrix)
        directrix_type = (
            directrix.attrib[self.type] if self.type in directrix.attrib else directrix.tag
        )
        dim = self.IfcDimensionSize(directrix, directrix_type)
        if dim != 3:
            return "The Directrix shall be a curve in three dimensional space"


    def DirectrixIsPolyline(self, entity, ifcname, called_entity=None):
        """Checks if the directrix is a polyline or indexed poly curve with no segments.
        ----------
        This is used in IfcSweptDiskSolidPolygonal."""
        directrix = entity.find("Directrix")
        if "ref" in directrix.attrib:
            directrix = self.ref_check(directrix)
        directrix_type = (
            directrix.attrib[self.type] if self.type in directrix.attrib else directrix.tag
        )
        if not self.attr_check(directrix_type, "IfcPolyline"):
            error_msg = "The Directrix shall be of type IfcIndexedPolyCurve with no Segments, "\
                "or of type IfcPolyline"
            if not self.attr_check(directrix_type, "IfcIndexedPolyCurve"):
                return error_msg
            else:
                if directrix.find("Segments") is not None:
                    return error_msg


    def DistinctSurfaces(self, entity, ifcname, called_entity=None):
        """Checks if two associated geometry elements are related to distinct surfaces.
        ----------
        This is used in IfcIntersectionCurve."""
        geometry = entity.find("AssociatedGeometry")
        if "ref" in geometry.attrib:
            geometry = self.ref_check(geometry)
        if "ref" in geometry[0].attrib:
            geometry[0] = self.ref_check(geometry[0])
        if "ref" in geometry[1].attrib:
            geometry[1] = self.ref_check(geometry[1])
        equal = self.elements_equal(geometry[0], geometry[1])
        if equal:
            return "The two associated geometry elements shall be related to distinct surfaces. "\
                "These are the surfaces which define the intersection curve"


    def EdgeElementNotOriented(self, entity, ifcname, called_entity=None):
        """Checks if the edge element is not an oriented edge.
        ----------
        This is used in IfcOrientedEdge."""
        edge = entity.find("EdgeElement")
        if "ref" in edge.attrib:
            edge = self.ref_check(edge)
        edge = edge.attrib[self.type] if self.type in edge.attrib else edge.tag
        if self.attr_check(edge, "IfcOrientedEdge"):
            return "The edge element shall not be an oriented edge"


    def ExistsName(self, entity, ifcname, called_entity=None):
        """Checks if the name attribute exists.
        ----------
        This is used in IfcPropertySet & IfcPropertySetTemplate."""
        if "Name" not in entity.attrib or entity.attrib["Name"] == "":
            return "The Name attribute has to be provided"


    def FirstOperandClosed(self, entity, ifcname, called_entity=None):
        """Checks if the first operand of a tessellated face set is closed.
        ----------
        This is used in IfcBooleanResult."""
        first_op = entity.find("FirstOperand")[0]
        if first_op.tag == "IfcTriangulatedFaceSet" or first_op.tag == "IfcPolygonalFaceSet":
            if "ref" in first_op.attrib:
                first_op = self.ref_check(first_op)
            if first_op.attrib["Closed"].lower() != "true":
                return "If the FirstOperand is of type IfcTessellatedFaceSet it has to be a "\
                    "closed tessellation"


    def FirstOperandType(self, entity, ifcname, called_entity=None):
        """Checks if the first operand of a boolean clipping operation is a swept area solid or
        a boolean result, in case of multiple clippings.
        ----------
        This is used in IfcBooleanClippingResult."""
        allowed_types = ["IfcSweptAreaSolid", "IfcSweptDiskSolid", "IfcBooleanResult"]
        first_op = entity.find("FirstOperand")[0].tag
        if not self.attr_list_check(first_op, allowed_types):
            return "The first operand of the Boolean clipping operation shall be either an "\
                "IfcSweptAreaSolid or (in case of more than one clipping) an IfcBooleanResult"


    def HasAdvancedFaces(self, entity, ifcname, called_entity=None):
        """Checks if each face of the advanced B-rep is of advanced face type.
        ----------
        This is used in IfcAdvancedBrep."""
        shell = entity.find("Outer")
        if "ref" in shell.attrib:
            shell = self.ref_check(shell)
        faces = shell.find("CfsFaces")
        for face in faces:
            if not self.attr_check(face.tag, "IfcAdvancedFace"):
                return "Each face of the advanced B-rep shall be of type IfcAdvancedFace"


    def HasDecomposition(self, entity, ifcname, called_entity=None):
        """Checks if the entity has parts in a decomposition hierarchy.
        ----------
        This is used in IfcSlabElementedCase & IfcWallElementedCase."""
        decomposition = entity.find("IsDecomposedBy")
        if decomposition is None:
            if ifcname == "IfcSlabElementedCase":
                return "A valid instance of IfcSlabElementedCase has to have parts in a "\
                    "decomposition hierarchy"
            elif ifcname == "IfcWallElementedCase":
                return "A valid instance of IfcWallElementedCase has to have parts in a "\
                    "decomposition hierarchy"


    def HasIdentifierOrName(self, entity, ifcname, called_entity=None):
        """Checks if either an identifier or name is given.
        ----------
        This is used in IfcApproval."""
        if ("Name" not in entity.attrib or entity.attrib["Name"] == "") and (
            "Identifier" not in entity.attrib or entity.attrib["Identifier"] == ""
        ):
            return "Either Identifier or Name (or both) by which the approval is known shall "\
                "be given"


    def HasMaterialLayerSetUsage(self, entity, ifcname, called_entity=None):
        """Checks if the material layer set usage is provided.
        ----------
        This is used in IfcPlateStandardCase, IfcSlabStandardCase & IfcWallStandardCase."""
        #Check for HasAssociates, since it is the only IfcRelAssociates entity in the
        #attribute inheritance.
        associations = entity.find("HasAssociations")
        real_associations = associations[0].find("RelatingMaterial")
        if "ref" in real_associations.attrib:
            real_associations = self.ref_check(real_associations)
        real_associations_type = (
            real_associations.attrib[self.type]
            if self.type in real_associations.attrib
            else real_associations.tag
        )
        if (
            associations[0].tag != "IfcRelAssociatesMaterial"
            or real_associations_type != "IfcMaterialLayerSetUsage"
        ):
            if ifcname in ("IfcPlateStandardCase", "IfcSlabStandardCase", "IfcWallStandardCase"):
                return (
                    "A valid instance of "
                    + ifcname
                    + " relies on the provision of an IfcMaterialLayerSetUsage"
                )


    def HasMaterialProfileSetUsage(self, entity, ifcname, called_entity=None):
        """Checks if the material profile set usage is provided.
        ----------
        This is used in IfcBeamStandardCase, IfcColumnStandardCase & IfcMemberStandardCase."""
        #Check for HasAssociates, since it is the only IfcRelAssociates entity in the
        #attribute inheritance.
        associations = entity.find("HasAssociations")
        real_associations = associations[0].find("RelatingMaterial")
        if "ref" in real_associations.attrib:
            real_associations = self.ref_check(real_associations)
        real_associations_type = (
            real_associations.attrib[self.type]
            if self.type in real_associations.attrib
            else real_associations.tag
        )
        allowed_material = ["IfcMaterialProfileSetUsage", "IfcMaterialProfileSetUsageTapering"]
        if (
            associations[0].tag != "IfcRelAssociatesMaterial"
            or real_associations_type not in allowed_material
        ):
            if ifcname in ("IfcBeamStandardCase", "IfcColumnStandardCase", "IfcMemberStandardCase"):
                return (
                    "A valid instance of "
                    + ifcname
                    + " relies on the provision of an IfcMaterialProfileSetUsage"
                )


    def HasName(self, entity, ifcname, called_entity=None):
        """Checks if a name is given.
        ----------
        This is used in IfcProcedure, IfcProject & IfcTask."""
        if "Name" not in entity.attrib or entity.attrib["Name"] == "":
            return "Name attribute has to be given"


    def HasNoSubtraction(self, entity, ifcname, called_entity=None):
        """Checks if a feature subtraction has no other openings.
        ----------
        This is used in IfcFeatureElementSubtraction."""
        if entity.find("HasOpenings") is not None:
            return "An feature subtraction (e.g. an opening element) can not have other openings "\
                "to void itself"


    def HasObjectName(self, entity, ifcname, called_entity=None):
        """Checks if an object name is given.
        ----------
        This is used in IfcBuildingElementProxy."""
        if "Name" not in entity.attrib or entity.attrib["Name"] == "":
            return "Name attribute has to be given"


    def HasObjectType(self, entity, ifcname, called_entity=None):
        """Checks if the object type is given, if the predefined type is set to userdefined.
        ----------
        This is used in IfcStructuralAnalysisModel, IfcStructuralCurveAction,
        IfcStructuralCurveMember, IfcStructuralCurveReaction, IfcStructuralLoadGroup,
        IfcStructuralResultGroup, IfcStructuralSurfaceAction, IfcStructuralSurfaceMember,
        IfcSurfaceFeature & IfcVoidingFeature."""
        if ifcname in ("IfcSurfaceFeature", "IfcVoidingFeature"):
            if "PredefinedType" in entity.attrib:
                if entity.attrib["PredefinedType"].lower() == "userdefined":
                    if "ObjectType" not in entity.attrib or entity.attrib["ObjectType"] == "":
                        return "The attribute ObjectType shall be given if the predefined type "\
                            "is set to USERDEFINED"
        elif ifcname == "IfcStructuralLoadGroup":
            if (
                entity.attrib["PredefinedType"].lower() == "userdefined"
                or entity.attrib["ActionType"].lower() == "userdefined"
                or entity.attrib["ActionSource"].lower() == "userdefined"
            ):
                if "ObjectType" not in entity.attrib or entity.attrib["ObjectType"] == "":
                    return "The attribute ObjectType shall be given if the predefined type, "\
                        "action type, or action source is set to USERDEFINED"
        elif ifcname == "IfcStructuralResultGroup":
            if entity.attrib["TheoryType"].lower() == "userdefined":
                if "ObjectType" not in entity.attrib or entity.attrib["ObjectType"] == "":
                    return "The attribute ObjectType shall be given if the analysis theory type "\
                        "is set to USERDEFINED."
        else:
            if entity.attrib["PredefinedType"].lower() == "userdefined":
                if "ObjectType" not in entity.attrib or entity.attrib["ObjectType"] == "":
                    return "The attribute ObjectType shall be given if the predefined type is "\
                        "set to USERDEFINED"


    def HasOuterBound(self, entity, ifcname, called_entity=None):
        """Checks if maximum one of the bounds is a face outer bound.
        ----------
        This is used in IfcFace."""
        bounds = entity.find("Bounds")
        count = 0
        for bound in bounds:
            if bound.tag == "IfcFaceOuterBound":
                count = count + 1
                if count > 1:
                    return "At most one of the bounds shall be of the type IfcFaceOuterBound"


    def HasPlacement(self, entity, ifcname, called_entity=None):
        """Checks if an object placement entity is given.
        ----------
        This is used in IfcGrid."""
        placement = entity.find("ObjectPlacement")
        if placement is None:
            return "The object placement has to be given"


    def HasPredefinedType(self, entity, ifcname, called_entity=None):
        """Checks if the object type is given, when the predefined type is set to userdefined.
        ----------
        This is used in IfcStructuralSurfaceReaction."""
        if entity.attrib["PredefinedType"].lower() == "userdefined":
            if "ObjectType" not in entity.attrib or entity.attrib["ObjectType"] == "":
                return "The attribute ObjectType shall be given if the predefined type is set "\
                    "to USERDEFINED"


    def HasRepresentationIdentifier(self, entity, ifcname, called_entity=None):
        """Checks if a representation identifier is provided.
        ----------
        This is used in IfcShapeRepresentation."""
        if (
            "RepresentationIdentifier" not in entity.attrib
            or entity.attrib["RepresentationIdentifier"] == ""
        ):
            return "A representation identifier should be provided for the shape representation"


    def HasRepresentationType(self, entity, ifcname, called_entity=None):
        """Checks if a representation type is provided.
        ----------
        This is used in IfcShapeRepresentation."""
        if "RepresentationType" not in entity.attrib or entity.attrib["RepresentationType"] == "":
            return "A representation type should be provided for the shape representation"


    def IdentifiableCurveStyle(self, entity, ifcname, called_entity=None):
        """Checks if at least one of (curve font, width, colour) attribute is provided.
        ----------
        This is used in IfcCurveStyle."""
        if (
            entity.find("CurveFont") is None
            and entity.find("CurveWidth") is None
            and entity.find("CurveColour") is None
        ):
            return "At minimum one of the three attribute values have to be provided, CurveFont, "\
                "CurveWidth, CurveColour"


    def IdentifiablePerson(self, entity, ifcname, called_entity=None):
        """Checks if minimum informations about a person to be identified are given.
        ----------
        This is used in IfcPerson."""
        if not (
            ("Identification" in entity.attrib and entity.attrib["Identification"] != "")
            or ("FamilyName" in entity.attrib and entity.attrib["FamilyName"] != "")
            or ("GivenName" in entity.attrib and entity.attrib["GivenName"] != "")
        ):
            return "Requires that the identification or/and the family name or/and the given "\
                "name is provided as minimum information"


    def InnerRadiusSize(self, entity, ifcname, called_entity=None):
        """Checks if outer radius is greater than the inner radius, if an inner radius is provided.
        ----------
        This is used in IfcSweptDiskSolid."""
        if "InnerRadius" in entity.attrib:
            if float(entity.attrib["InnerRadius"]) >= float(entity.attrib["Radius"]):
                return "If InnerRadius exists then Radius denoting the outer radius shall be "\
                    "greater than InnerRadius"


    def InvariantProfileType(self, entity, ifcname, called_entity=None):
        """Checks if the derived profile has the same type as the parent profile.
        ----------
        This is used in IfcCompositeProfileDef & IfcDerivedProfileDef."""
        if ifcname == "IfcCompositeProfileDef":
            profiles = entity.find("Profiles")
            if "ref" in profiles[0].attrib:
                profiles[0] = self.ref_check(profiles[0])
            used_type = profiles[0].attrib["ProfileType"].lower()
            for profile in profiles:
                if "ref" in profile.attrib:
                    profile = self.ref_check(profile)
                if profile.attrib["ProfileType"].lower() != used_type:
                    return "Either all profiles are areas or all profiles are curves"
        elif ifcname == "IfcDerivedProfileDef":
            profile_type = entity.attrib["ProfileType"].lower()
            parent = entity.find("ParentProfile")
            if "ref" in parent.attrib:
                parent = self.ref_check(parent)
            parent_type = parent.attrib["ProfileType"].lower()
            if profile_type != parent_type:
                return "The profile type of the derived profile shall be the same as the type of "\
                    "the parent profile, i.e. both shall be either AREA or CURVE"


    def IsClosed(self, entity, ifcname, called_entity=None):
        """Checks if the curve or edge loop is closed.
        ----------
        This is used in IfcBoundaryCurve & IfcEdgeLoop."""
        if ifcname == "IfcBoundaryCurve":
            segments = entity.find("Segments")
            if "ref" in segments[len(segments) - 1].attrib:
                segment = self.ref_check(segments[len(segments) - 1])
            else:
                segment = segments[len(segments) - 1]
            if segment.attrib["Transition"].lower() == "discontinuous":
                return "The derived ClosedCurve attribute of IfcCompositeCurve supertype shall "\
                    "be TRUE"
        elif ifcname == "IfcEdgeLoop":
            edges = entity.find("EdgeList")
            if "ref" in edges[0].attrib:
                edges[0] = self.ref_check(edges[0])
            if "ref" in edges[-1].attrib:
                edges[-1] = self.ref_check(edges[-1])
            start_edge_element = edges[0].find("EdgeElement")
            if "ref" in start_edge_element.attrib:
                start_edge_element = self.ref_check(start_edge_element)
            if edges[0].attrib["Orientation"].lower() == "true":
                start_element = start_edge_element.find("EdgeStart")
                if "ref" in start_element.attrib:
                    start_element = self.ref_check(start_element)
            else:
                start_element = start_edge_element.find("EdgeEnd")
                if "ref" in start_element.attrib:
                    start_element = self.ref_check(start_element)
            end_edge_element = edges[-1].find("EdgeElement")
            if "ref" in end_edge_element.attrib:
                end_edge_element = self.ref_check(end_edge_element)
            if edges[-1].attrib["Orientation"].lower() == "true":
                end_element = end_edge_element.find("EdgeEnd")
                if "ref" in end_element.attrib:
                    end_element = self.ref_check(end_element)
            else:
                end_element = end_edge_element.find("EdgeStart")
                if "ref" in end_element.attrib:
                    end_element = self.ref_check(end_element)
            if "id" in start_element.attrib:
                start_id = start_element.attrib["id"]
            else:
                start_id = start_element.attrib["ref"]
            if "id" in end_element.attrib:
                end_id = end_element.attrib["id"]
            else:
                end_id = end_element.attrib["ref"]

            if start_id != end_id:
                return "The start vertex of the first edge shall be the same as the end vertex "\
                    "of the last edge. This ensures that the path is closed to form a loop"


    def IsContinuous(self, entity, ifcname, called_entity=None):
        """Checks if the elements of the edge loop or path are continuous.
        ----------
        This is used in IfcEdgeLoop & IfcPath."""
        edges = entity.find("EdgeList")
        for i in range(len(edges) - 1):
            if "ref" in edges[i].attrib:
                edges[i] = self.ref_check(edges[i])
            if "ref" in edges[i + 1].attrib:
                edges[i + 1] = self.ref_check(edges[i + 1])
            current_edge_element = edges[i].find("EdgeElement")
            if "ref" in current_edge_element.attrib:
                current_edge_element = self.ref_check(current_edge_element)
            if edges[i].attrib["Orientation"].lower() == "true":
                current_edge = current_edge_element.find("EdgeEnd")
                if "ref" in current_edge.attrib:
                    current_edge = self.ref_check(current_edge)
            else:
                current_edge = current_edge_element.find("EdgeStart")
                if "ref" in current_edge.attrib:
                    current_edge = self.ref_check(current_edge)
            successor_element = edges[i + 1].find("EdgeElement")
            if "ref" in successor_element.attrib:
                successor_element = self.ref_check(successor_element)
            if edges[i + 1].attrib["Orientation"].lower() == "true":
                successor = successor_element.find("EdgeStart")
                if "ref" in successor.attrib:
                    successor = self.ref_check(successor)
            else:
                successor = successor_element.find("EdgeEnd")
                if "ref" in successor.attrib:
                    successor = self.ref_check(successor)

            if "id" in current_edge.attrib:
                current_id = current_edge.attrib["id"]
            else:
                current_id = current_edge.attrib["ref"]
            if "id" in successor.attrib:
                successor_id = successor.attrib["id"]
            else:
                successor_id = successor.attrib["ref"]
            if current_id != successor_id:
                return "The end vertex of each edge shall be the same as the start vertex of "\
                    "its successor"


    def IsLengthUnit(self, entity, ifcname, called_entity=None):
        """Checks if the lengthunit is chosen as unit type for a map unit, if given.
        ----------
        This is used in IfcProjectedCRS."""
        mapunit = entity.find("MapUnit")
        if mapunit is not None:
            if "ref" in mapunit.attrib:
                mapunit = self.ref_check(mapunit)
            if mapunit.attrib["UnitType"].lower() != "lengthunit":
                return "The map unit shall be given, if present, as a length unit"


    def IsLoadCasePredefinedType(self, entity, ifcname, called_entity=None):
        """Checks if the predefined type is a load case.
        ----------
        This is used in IfcStructuralLoadCase."""
        if entity.attrib["PredefinedType"].lower() != "load_case":
            return "An instance of this subtype of structural load group cannot be of any other "\
                "type than that of a load case"


    def IsNotFilling(self, entity, ifcname, called_entity=None):
        """Checks if a feature subtraction does not fill another void.
        ----------
        This is used in IfcFeatureElementSubtraction."""
        if entity.find("FillsVoids") is not None:
            return "An feature subtraction (e.g. an opening element) can not be a filling of "\
                "another void"


    def LocationIs3D(self, entity, ifcname, called_entity=None):
        """Checks if the location is 3D.
        ----------
        This is used in IfcAxis1Placement & IfcAxis2Placement3D."""
        location = entity.find("Location")
        if "ref" in location.attrib:
            location = self.ref_check(location)
        if len(re.split(r"\s+", location.attrib["Coordinates"])) != 3:
            return "The cartesian point describing the location has to be 3D"


    def MagGreaterOrEqualZero(self, entity, ifcname, called_entity=None):
        """Checks if the magnitude is not negative.
        ----------
        This is used in IfcVector."""
        if float(entity.attrib["Magnitude"]) < 0:
            return "The magnitude shall be positive or zero"


    def MagnitudeGreaterZero(self, entity, ifcname, called_entity=None):
        """Checks if the magnitude of the direction vector is greater than zero.
        ----------
        This is used in IfcDirection."""
        ratios = re.split(r"\s+", entity.attrib["DirectionRatios"])
        magnitude_rule = False
        for ratio in ratios:
            if float(ratio) != 0:
                magnitude_rule = True
                break
        if not magnitude_rule:
            return "The magnitude of the direction vector shall be greater than zero"


    def MajorLargerMinor(self, entity, ifcname, called_entity=None):
        """Checks if the major radius is bigger than the minor radius.
        ----------
        This is used in IfcToroidalSurface."""
        if float(entity.attrib["MajorRadius"]) <= float(entity.attrib["MinorRadius"]):
            return "The attribute value of the MinorRadius shall be smaller then the value of "\
                "the MajorRadius"


    def MaxOneColour(self, entity, ifcname, called_entity=None):
        """Checks if not more than one colour is assigned to fill an area style.
        ----------
        This is used in IfcFillAreaStyle."""
        count = 0
        restrict = ["IfcColour", "IfcColourSpecification", "IfcPreDefinedColour"]
        fill_styles = entity.find("FillStyles")
        for style in fill_styles:
            if style.tag in restrict:
                count = count + 1
            else:
                if (
                    style.tag in self.entities and
                    len(set(self.entities[style.tag]["supertypes"]).intersection(set(restrict)))
                        != 0
                    ):
                    count = count + 1
            if count > 1:
                return "There shall be a maximum of one colour assignment to the fill area style"


    def MaxOneExtDefined(self, entity, ifcname, called_entity=None):
        """Checks if an externally defined surface style is not used multiple times.
        ----------
        This is used in IfcSurfaceStyle."""
        styles = entity.find("Styles")
        count = 0
        for style in styles:
            if style.tag == "IfcExternallyDefinedSurfaceStyle":
                count = count + 1
                if count > 1:
                    return "The IfcExternallyDefinedSurfaceStyle shall only be used zero or one "\
                        "time within the set of Styles"


    def MaxOneExtHatchStyle(self, entity, ifcname, called_entity=None):
        """Checks if not more than one externally defined hatch style is assigned to fill an area.
        ----------
        This is used in IfcFillAreaStyle."""
        count = 0
        fill_styles = entity.find("FillStyles")
        for style in fill_styles:
            if style.tag == "IfcExternallyDefinedHatchStyle":
                count = count + 1
                if count > 1:
                    return "There shall be a maximum of one externally defined hatch style "\
                        "assignment to the fill area style"


    def MaxOneLighting(self, entity, ifcname, called_entity=None):
        """Checks if the surface style lighting is not used multiple times within the styles set.
        ----------
        This is used in IfcSurfaceStyle."""
        styles = entity.find("Styles")
        count = 0
        for style in styles:
            if style.tag == "IfcSurfaceStyleLighting":
                count = count + 1
                if count > 1:
                    return "The IfcSurfaceStyleLighting shall only be used zero or one time "\
                        "within the set of Styles"


    def MaxOneMaterialAssociation(self, entity, ifcname, called_entity=None):
        """Checks if not multiple material associations are assigned to an building element.
        ----------
        This is used in IfcBuildingElement."""
        associations = entity.find("HasAssociations")
        if associations is not None:
            if len(associations) > 1:
                return "There should be only a maximum of one material association assigned to "\
                    "an building element"


    def MaxOneRefraction(self, entity, ifcname, called_entity=None):
        """Checks if the surface style refraction is not used multiple times within a style set.
        ----------
        This is used in IfcSurfaceStyle."""
        styles = entity.find("Styles")
        count = 0
        for style in styles:
            if style.tag == "IfcSurfaceStyleRefraction":
                count = count + 1
                if count > 1:
                    return "The IfcSurfaceStyleRefraction shall only be used zero or one time "\
                        "within the set of Styles"


    def MaxOneShading(self, entity, ifcname, called_entity=None):
        """Checks if the surface style shading is not used multiple times within a style set.
        ----------
        This is used in IfcSurfaceStyle."""
        styles = entity.find("Styles")
        count = 0
        for style in styles:
            if style.tag == "IfcSurfaceStyleShading" or style.tag == "IfcSurfaceStyleRendering":
                count = count + 1
                if count > 1:
                    return "The IfcSurfaceStyleShading shall only be used zero or one time "\
                        "within the set of Styles"


    def MaxOneTextures(self, entity, ifcname, called_entity=None):
        """Checks if surface style with textures is not used multiple times within a style set.
        ----------
        This is used in IfcSurfaceStyle."""
        styles = entity.find("Styles")
        count = 0
        for style in styles:
            if style.tag == "IfcSurfaceStyleWithTextures":
                count = count + 1
                if count > 1:
                    return "The IfcSurfaceStyleWithTextures shall only be used zero or one time "\
                        "within the set of Styles"


    def MeasureOfFontSize(self, entity, ifcname, called_entity=None):
        """Checks if the font size has a positive length measure.
        ----------
        This is used in IfcTextStyleFontModel."""
        size = entity.find("FontSize")
        if size[0].tag != "IfcLengthMeasure-wrapper" or float(size[0].text) <= 0:
            return "The size should be given by a positive length measure"


    def MeasureOfWidth(self, entity, ifcname, called_entity=None):
        """Checks if the width measure is is positive or, if descriptive, the value should be
        'by layer'.
        ----------
        This is used in IfcCurveStyle."""
        width = entity.find("CurveWidth")
        if width is not None:
            if "ref" in width.attrib:
                width = self.ref_check(width)
            if (
                width.find("IfcPositiveLengthMeasure-wrapper") is None
                and (
                    width.find("IfcDescriptiveMeasure-wrapper") is None
                    or width.find("IfcDescriptiveMeasure-wrapper").text != "by layer"
                )
            ):
                return "The curve width, if provided, shall be given by an "\
                    "IfcPositiveLengthMeasure representing the curve width in the default "\
                    "measure unit, or by an IfcDescriptiveMeasure with the value 'by layer' "\
                    "representing the curve width by the default curve width at the "\
                    "associated layer"


    def MinPixelInS(self, entity, ifcname, called_entity=None):
        """Checks if the minimum number of pixels is 1.
        ----------
        This is used in IfcPixelTexture."""
        if int(entity.attrib["Width"]) < 1:
            return "The minimum number of pixel in width direction must be 1"


    def MinPixelInT(self, entity, ifcname, called_entity=None):
        """Checks if the minimum number of pixels is 1.
        ----------
        This is used in IfcPixelTexture."""
        if int(entity.attrib["Height"]) < 1:
            return "The minimum number of pixel in width direction must be 1"


    def MinimumDataProvided(self, entity, ifcname, called_entity=None):
        """Checks if the minimum amount of data is provided for a telecom address.
        ----------
        This is used in IfcTelecomAddress."""
        data_list = [
            "TelephoneNumbers",
            "FacsimileNumbers",
            "PagerNumber",
            "ElectronicMailAddresses",
            "WWWHomePageURL",
            "MessagingIDs",
        ]
        data_provided = False
        for data in data_list:
            if (data in entity.attrib and entity.attrib[data] != "") or entity.find(
                data
            ) is not None:
                data_provided = True
                break
        if not data_provided:
            return "Requires that at least one attribute of telephone numbers, "\
                "facsimile numbers, pager number, electronic mail addresses, "\
                "world wide web home page URL, or messaging ID is asserted"


    def NameRequired(self, entity, ifcname, called_entity=None):
        """Checks if the name attribute is given.
        ----------
        This is used in IfcTypeObject."""
        if "Name" not in entity.attrib or entity.attrib["Name"] == "":
            return "Name attribute has to be given"


    def NoCoordOperation(self, entity, ifcname, called_entity=None):
        """Checks if no coordinate operation is provided.
        ----------
        This is used in IfcGeometricRepresentationSubContext."""
        if entity.find("HasCoordinateOperation") is not None:
            return "An IfcCoordinateOperation shall not be provided to a geometric "\
                "representation sub context, only to the parent geometric representation context"


    def NoDecomposition(self, entity, ifcname, called_entity=None):
        """Checks if a project is not used to decompose any other object definition.
        ----------
        This is used in IfcProject."""
        decomposition = entity.find("Decomposes")
        if decomposition is not None:
            return "The IfcProject represents the root of the any decomposition tree. It shall "\
                "therefore not be used to decompose any other object definition"


    def NoRecursion(self, entity, ifcname, called_entity=None):
        """Checks if a composite profile does not include other composite profiles.
        ----------
        This is used in IfcCompositeProfileDef."""
        profiles = entity.find("Profiles")
        for profile in profiles:
            if profile.tag == "IfcCompositeProfileDef":
                return "A composite profile should not include another composite profile, "\
                    "i.e. no recursive definitions should be allowed"


    def NoRelatedTypeObject(self, entity, ifcname, called_entity=None):
        """Checks if no related object is of type IfcTypeObject.
        ----------
        This is used in IfcRelDefinesByProperties."""
        error_msg = "There shall be no related object being of type IfcTypeObject"
        if called_entity != "RelatedObjects":
            rel_objects = entity.find("RelatedObjects")
            if rel_objects is None:
                rel_objects = []
                identifier = entity.attrib["id"]
                referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                if len(referenced) > 0:
                    for ref in referenced:
                        if ref.getparent().tag == "IsDefinedBy":
                            rel_objects.append(ref.getparent().getparent())
            for rel_object in rel_objects:
                rel_object_type = (
                    rel_object.attrib[self.type]
                    if self.type in rel_object.attrib
                    else rel_object.tag
                )
                if self.attr_check(rel_object_type, "IfcTypeObject"):
                    return error_msg

        else:
            rel_object = entity.getparent().getparent()
            rel_object_type = (
                rel_object.attrib[self.type] if self.type in rel_object.attrib else rel_object.tag
            )
            if self.attr_check(rel_object_type, "IfcTypeObject"):
                return error_msg


    def NoSelfReference(self, entity, ifcname, called_entity=None):
        """Checks if an entity does not reference itself.
        ----------
        This is used in IfcComplexPropertyTemplate, IfcRelAggregates, IfcRelAssignsToActor,
        IfcRelAssignsToControl, IfcRelAssignsToGroup, IfcRelAssignsToProcess,
        IfcRelAssignsToProduct, IfcRelAssignsToResource, IfcRelDeclares, IfcRelNests,
        IfcRelConnectsElements, IfcRelConnectsPorts, IfcRelInterferesElements,
        IfcPropertyDependencyRelationship & IfcPhysicalComplexQuantity."""
        rel_single_list = [
            "IfcRelConnectsElements",
            "IfcRelConnectsPorts",
            "IfcRelInterferesElements",
            "IfcPropertyDependencyRelationship",
        ]
        if ifcname in rel_single_list:
            if ifcname in ("IfcRelConnectsElements", "IfcRelInterferesElements"):
                relating = (
                    entity.getparent().getparent()
                    if called_entity == "RelatingElement"
                    else entity.find("RelatingElement")
                )
                related = (
                    entity.getparent().getparent()
                    if called_entity == "RelatedElement"
                    else entity.find("RelatedElement")
                )
            elif ifcname == "IfcRelConnectsPorts":
                relating = (
                    entity.getparent().getparent()
                    if called_entity == "RelatingPort"
                    else entity.find("RelatingPort")
                )
                related = (
                    entity.getparent().getparent()
                    if called_entity == "RelatedPort"
                    else entity.find("RelatedPort")
                )
            elif ifcname == "IfcPropertyDependencyRelationship":
                relating = (
                    entity.getparent().getparent()
                    if called_entity == "DependingProperty"
                    else entity.find("DependingProperty")
                )
                related = (
                    entity.getparent().getparent()
                    if called_entity == "DependantProperty"
                    else entity.find("DependantProperty")
                )

            if relating is None:
                find = False
                identifier = entity.attrib["id"]
                referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                called_as = self.entities[ifcname]["called_as"]
                if len(referenced) > 0:
                    for ref in referenced:
                        if ref.tag in called_as:
                            for l, call in enumerate(called_as):
                                if call == ref.tag:
                                    rel = self.entities[ifcname]["called_corresponding_entity"][l]
                                    if rel.startswith("Relating") or rel.startswith("Relating"):
                                        relating = ref.getparent()
                                        find = True
                                        break
                            if find:
                                break

            if "id" in relating.attrib:
                relating_id = relating.attrib["id"]
            else:
                relating_id = relating.attrib["ref"]

            if related is None:
                find = False
                identifier = entity.attrib["id"]
                referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                called_as = self.entities[ifcname]["called_as"]
                if len(referenced) > 0:
                    for ref in referenced:
                        if ref.tag in called_as:
                            for l, call in enumerate(called_as):
                                if call == ref.tag:
                                    rel = self.entities[ifcname]["called_corresponding_entity"][l]
                                    if rel.startswith("Related") or rel.startswith("Dependant"):
                                        related = ref.getparent()
                                        find = True
                                        break
                            if find:
                                break

            if "id" in related.attrib:
                related_id = related.attrib["id"]
            else:
                related_id = related.attrib["ref"]

            if relating_id == related_id:
                return "No self reference is allowed"

        elif ifcname == "IfcComplexPropertyTemplate":
            current_id = entity.attrib["id"]
            templates = entity.find("HasPropertyTemplates")
            if templates is not None:
                for template in templates:
                    if "ref" in template.attrib:
                        if template.attrib["ref"] == current_id:
                            return "The IfcComplexPropertyTemplate should not reference itself "\
                                "within the list of HasPropertyTemplates"
            else:
                #The current_id has to be different than the one from where it was called
                #(because a parent item can't be a referenced one)
                pass

        elif ifcname == "IfcPhysicalComplexQuantity":
            current_id = entity.attrib["id"]
            quantities = entity.find("HasQuantities")
            if quantities is not None:
                for quantity in quantities:
                    if "ref" in quantity.attrib:
                        if quantity.attrib["ref"] == current_id:
                            return "The IfcPhysicalComplexQuantity should not reference itself "\
                                "within the list of HasQuantities"
            else:
                #The current_id has to be different than the one from where it was called
                #(because a parent item can't be a referenced one)
                pass

        else:
            if ifcname in ("IfcRelAggregates", "IfcRelNests"):
                relating = (
                    entity.getparent().getparent()
                    if called_entity == "RelatingObject"
                    else entity.find("RelatingObject")
                )
                rel_objects = (
                    [entity.getparent().getparent()]
                    if called_entity == "RelatedObjects"
                    else entity.find("RelatedObjects")
                )
            elif ifcname == "IfcRelAssignsToActor":
                relating = (
                    entity.getparent().getparent()
                    if called_entity == "RelatingActor"
                    else entity.find("RelatingActor")
                )
                rel_objects = (
                    [entity.getparent().getparent()]
                    if called_entity == "RelatedObjects"
                    else entity.find("RelatedObjects")
                )
            elif ifcname == "IfcRelAssignsToControl":
                relating = (
                    entity.getparent().getparent()
                    if called_entity == "RelatingControl"
                    else entity.find("RelatingControl")
                )
                rel_objects = (
                    [entity.getparent().getparent()]
                    if called_entity == "RelatedObjects"
                    else entity.find("RelatedObjects")
                )
            elif ifcname == "IfcRelAssignsToGroup":
                relating = (
                    entity.getparent().getparent()
                    if called_entity == "RelatingGroup"
                    else entity.find("RelatingGroup")
                )
                rel_objects = (
                    [entity.getparent().getparent()]
                    if called_entity == "RelatedObjects"
                    else entity.find("RelatedObjects")
                )
            elif ifcname == "IfcRelAssignsToProcess":
                relating = (
                    entity.getparent().getparent()
                    if called_entity == "RelatingProcess"
                    else entity.find("RelatingProcess")[0]
                )
                rel_objects = (
                    [entity.getparent().getparent()]
                    if called_entity == "RelatedObjects"
                    else entity.find("RelatedObjects")
                )
            elif ifcname == "IfcRelAssignsToProduct":
                relating = (
                    entity.getparent().getparent()
                    if called_entity == "RelatingProduct"
                    else entity.find("RelatingProduct")[0]
                )
                rel_objects = (
                    [entity.getparent().getparent()]
                    if called_entity == "RelatedObjects"
                    else entity.find("RelatedObjects")
                )
            elif ifcname == "IfcRelAssignsToResource":
                relating = (
                    entity.getparent().getparent()
                    if called_entity == "RelatingResource"
                    else entity.find("RelatingResource")[0]
                )
                rel_objects = (
                    [entity.getparent().getparent()]
                    if called_entity == "RelatedObjects"
                    else entity.find("RelatedObjects")
                )
            elif ifcname == "IfcRelDeclares":
                relating = (
                    entity.getparent().getparent()
                    if called_entity == "RelatingContext"
                    else entity.find("RelatingContext")
                )
                rel_objects = (
                    [entity.getparent().getparent()]
                    if called_entity == "RelatedDefinitions"
                    else entity.find("RelatedDefinitions")
                )

            if relating is None:
                find = False
                identifier = entity.attrib["id"]
                referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                called_as = self.entities[ifcname]["called_as"]
                if len(referenced) > 0:
                    for ref in referenced:
                        if ref.tag in called_as or ref.getparent().tag in called_as:
                            for l, call in enumerate(called_as):
                                if call in (ref.tag, ref.getparent().tag):
                                    rel = self.entities[ifcname]["called_corresponding_entity"][l]
                                    if rel.startswith("Relating"):
                                        relating = (
                                            ref.getparent()
                                            if call == ref.tag
                                            else ref.getparent().getparent()
                                        )
                                        find = True
                                        break
                            if find:
                                break

            if "id" in relating.attrib:
                relating_id = relating.attrib["id"]
            else:
                relating_id = relating.attrib["ref"]

            if rel_objects is None:
                find = False
                identifier = entity.attrib["id"]
                referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                called_as = self.entities[ifcname]["called_as"]
                if len(referenced) > 0:
                    for ref in referenced:
                        if ref.tag in called_as or ref.getparent().tag in called_as:
                            for l, call in enumerate(called_as):
                                if call in (ref.tag, ref.getparent().tag):
                                    rel = self.entities[ifcname]["called_corresponding_entity"][l]
                                    if rel.startswith("Related"):
                                        related = (
                                            ref.getparent()
                                            if call == ref.tag
                                            else ref.getparent().getparent()
                                        )
                                        find = True
                                        break
                            if find:
                                break

                if "id" in related.attrib:
                    related_id = related.attrib["id"]
                else:
                    related_id = related.attrib["ref"]

                if relating_id == related_id:
                    return "No self reference is allowed"

            else:
                for rel_object in rel_objects:
                    if "id" in rel_object.attrib:
                        rel_object_id = rel_object.attrib["id"]
                    else:
                        rel_object_id = rel_object.attrib["ref"]

                    if relating_id == rel_object_id:
                        return "No self reference is allowed"


    def NoSurfaces(self, entity, ifcname, called_entity=None):
        """Checks if no surface is included in a geometric set.
        ----------
        This is used in IfcGeometricCurveSet."""
        elements = entity.find("Elements")
        for element in elements:
            if self.attr_check(element.tag, "IfcSurface"):
                return "No surface shall be included in this geometric set."


    def NoTopologicalItem(self, entity, ifcname, called_entity=None):
        """Checks if no topological item is used.
        ----------
        This is used in IfcShapeRepresentation."""
        allowed_topological = ["IfcVertexPoint", "IfcEdgeCurve", "IfcFaceSurface"]
        items = entity.find("Items")
        for item in items:
            if (
                self.attr_check(item.tag, "IfcTopologicalRepresentationItem")
                and not self.attr_list_check(item.tag, allowed_topological)
            ):
                return "No topological representation item shall be directly used for shape "\
                    "representations, with the exception of IfcVertexPoint, IfcEdgeCurve, "\
                    "IfcFaceSurface"


    def NoTrimOfBoundedCurves(self, entity, ifcname, called_entity=None):
        """Checks if bounded curves are not trimmed.
        ----------
        This is used in IfcTrimmedCurve."""
        curve = entity.find("BasisCurve")
        if "ref" in curve.attrib:
            curve = self.ref_check(curve)
        curve = curve.attrib[self.type] if self.type in curve.attrib else curve.tag
        if self.attr_check(curve, "IfcBoundedCurve"):
            return "Already bounded curves shall not be trimmed"


    def NoVoidElement(self, entity, ifcname, called_entity=None):
        """Checks if no void element is given.
        ----------
        This is used in IfcRelAssociatesMaterial."""
        rel_objects = (
            [entity.getparent().getparent()]
            if called_entity == "RelatedObjects"
            else entity.find("RelatedObjects")
        )
        if rel_objects is None:
            rel_objects = []
            identifier = entity.attrib["id"]
            referenced = self.tree.findall(f".//*[@ref='{identifier}']")
            if len(referenced) > 0:
                for ref in referenced:
                    if ref.getparent().tag == "AssociatedTo":
                        rel_objects.append(ref.getparent().getparent())
        for rel_object in rel_objects:
            rel_object_type = (
                rel_object.attrib[self.type] if self.type in rel_object.attrib else rel_object.tag
            )
            if rel_object_type in (
                "IfcFeatureElementSubtraction",
                "IfcVirtualElement",
                "IfcOpeningElement",
                "IfcVoidingFeature",
            ):
                return "Material information cannot be associated to a " + rel_object_type + ""


    def NonnegativeArea1(self, entity, ifcname, called_entity=None):
        """Checks if the surface reinforcement area is positive.
        ----------
        This is used in IfcSurfaceReinforcementArea."""
        if "SurfaceReinforcement1" in entity.attrib:
            reinforcement = re.split(r"\s+", entity.attrib["SurfaceReinforcement1"])
            for r in reinforcement:
                if r < 0:
                    return "Surface reinforcement area must not be less than 0"


    def NonnegativeArea2(self, entity, ifcname, called_entity=None):
        """Checks if the surface reinforcement area is positive.
        ----------
        This is used in IfcSurfaceReinforcementArea."""
        if "SurfaceReinforcement2" in entity.attrib:
            reinforcement = re.split(r"\s+", entity.attrib["SurfaceReinforcement2"])
            for r in reinforcement:
                if r < 0:
                    return "Surface reinforcement area must not be less than 0"


    def NonnegativeArea3(self, entity, ifcname, called_entity=None):
        """Checks if the surface reinforcement area is positive.
        ----------
        This is used in IfcSurfaceReinforcementArea."""
        if "ShearReinforcement2" in entity.attrib:
            if entity.attrib["ShearReinforcement"] < 0:
                return "Surface reinforcement area must not be less than 0"


    def NormalizedPriority(self, entity, ifcname, called_entity=None):
        """Checks if the priority is normalized (priority between 0 and 100).
        ----------
        This is used in IfcMaterialLayer & IfcMaterialProfile."""
        if "Priority" in entity.attrib:
            val = int(entity.attrib["Priority"])
            if 0 <= val <= 100:
                return "The Property shall all be given as a normalized integer range [0..100], "\
                    "where 0 is the lowest and 100 the highest priority"


    def North2D(self, entity, ifcname, called_entity=None):
        """Checks if given TrueNorth is 2D.
        ----------
        This is used in IfcGeometricRepresentationContext."""
        north = entity.find("TrueNorth")
        if north is not None:
            if "ref" in north.attrib:
                north = self.ref_check(north)
            if len(re.split(r"\s+", north.attrib["DirectionRatios"])) != 2:
                return "TrueNorth has to be 2D"


    def NumberOfColours(self, entity, ifcname, called_entity=None):
        """Checks if the number of color components is between 1 and 4 (and of type integer).
        ----------
        This is used in IfcPixelTexture."""
        if not 1 <= int(entity.attrib["ColourComponents"]) <= 4:
            return "The number of color components must be either 1, 2, 3, or 4"


    def OnlyShapeModel(self, entity, ifcname, called_entity=None):
        """Checks if the corresponding representation through IfcProductDefinitionShape is allowed.
        ----------
        This is used in IfcProductDefinitionShape."""
        representations = entity.find("Representations")
        for rep in representations:
            if not self.attr_check(rep.tag, "IfcShapeModel"):
                return "Only representations of type IfcShapeModel, i.e. either "\
                    "IfcShapeRepresentation or IfcTopologyRepresentation should be used "\
                    "to represent a product through the IfcProductDefinitionShape"


    def OnlyStyledItems(self, entity, ifcname, called_entity=None):
        """Checks if only styled items, or subtypes of it, are used in the list of items.
        ----------
        This is used in IfcStyledRepresentation."""
        items = entity.find("Items")
        for item in items:
            if not self.attr_check(item.tag, "IfcStyledItem"):
                return "Only IfcStyledItem's (or subtypes) are allowed as members in the list "\
                    "of Items, inherited from IfcRepresentation"


    def OnlyStyledRepresentations(self, entity, ifcname, called_entity=None):
        """Checks if a styled representation is used to represent material through material
        representation.
        ----------
        This is used in IfcMaterialDefinitionRepresentation."""
        representations = entity.find("Representations")
        for rep in representations:
            if not self.attr_check(rep.tag, "IfcStyledRepresentation"):
                return "Only representations of type IfcStyledRepresentation should be used "\
                    "to represent material through the IfcMaterialRepresentation"


    def OperatorType(self, entity, ifcname, called_entity=None):
        """Checks if the boolean operator for clipping is 'Difference'.
        ----------
        This is used in IfcBooleanClippingResult."""
        if entity.attrib["Operator"].lower() != "difference":
            return "The Boolean operator for clipping is always 'Difference'"


    def ParentIsBoundedCurve(self, entity, ifcname, called_entity=None):
        """Checks if the parent curve is bounded.
        ----------
        This is used in IfcCompositeCurveSegment."""
        parent = entity.find("ParentCurve")
        if "ref" in parent.attrib:
            parent = self.ref_check(parent)
        parent = parent.attrib[self.type] if self.type in parent.attrib else parent.tag
        if not self.attr_check(parent, "IfcBoundedCurve"):
            return "The parent curve shall be a bounded curve."


    def ParentNoSub(self, entity, ifcname, called_entity=None):
        """Checks if the parent is no sub context.
        ----------
        This is used in IfcGeometricRepresentationSubContext."""
        parent = (
            entity.getparent().getparent()
            if called_entity == "ParentContext"
            else entity.find("ParentContext")
        )
        count = 0
        if parent is None:
            identifier = entity.attrib["id"]
            referenced = self.tree.findall(f".//*[@ref='{identifier}']")
            if len(referenced) > 0:
                for ref in referenced:
                    if ref.getparent().tag == "HasSubContexts":
                        parent = ref.getparent().getparent()
                        count += 1

        if "ref" in parent.attrib:
            parent = self.ref_check(parent)
        parent_type = parent.attrib[self.type] if self.type in parent.attrib else parent.tag
        if parent_type == "IfcGeometricRepresentationSubContext":
            return "The parent context shall not be another geometric representation sub context"
        elif count > 1:
            return "Warning: This IfcGeometricRepresentationSubContext might have too many parents."


    def PatternStart2D(self, entity, ifcname, called_entity=None):
        """Checks if the pattern start is 2D.
        ----------
        This is used in IfcFillAreaStyleHatching."""
        pattern = entity.find("PatternStart")
        if pattern is not None:
            if "ref" in pattern.attrib:
                pattern = self.ref_check(pattern)
            if len(re.split(r"\s+", pattern.attrib["Coordinates"])) != 2:
                return "The IfcCartesianPoint, if given as value to PatternStart shall have the "\
                    "dimensionality of 2"


    def PixelAsByteAndSameLength(self, entity, ifcname, called_entity=None):
        """Checks if the amount of all pixels as byte have the same length.
        ----------
        This is used in IfcPixelTexture."""
        pixel_list = len(re.split(r"\s+", entity.attrib["Pixel"]))
        pixel_bytes = len(str(pixel_list[0]))
        if pixel_bytes % 8 != 0:
            return "The binary value provided for each Pixel shall be a multiple of 8 bits"
        else:
            for pixel in pixel_list:
                if len(str(pixel)) != pixel_bytes:
                    return "All pixel shall have the same binary length"


    def PlacementForShapeRepresentation(self, entity, ifcname, called_entity=None):
        """Checks if an object placement is given, if a representation is a shape representation.
        ----------
        This is used in IfcProduct & IfcBuildingStorey."""
        representation = (
            entity.getparent().getparent()
            if called_entity == "Representation"
            else entity.find("Representation")
        )
        placement = (
            entity.getparent().getparent()
            if called_entity == "ObjectPlacement"
            else entity.find("ObjectPlacement")
        )
        error_msg = "If a Representation is given being an IfcShapeRepresentation, then also an "\
            "ObjectPlacement has to be given. The ObjectPlacement defines the object coordinate "\
            "system in which the geometric representation items of the IfcShapeRepresentation "\
            "are founded"

        if representation is not None:
            if "ref" in representation.attrib:
                representation = self.ref_check(representation)
            representation_type = (
                representation.attrib[self.type]
                if self.type in representation.attrib
                else representation.tag
            )
            if representation_type == "IfcShapeRepresentation":
                if placement is None:
                    find = False
                    identifier = entity.attrib["id"]
                    referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                    if len(referenced) > 0:
                        for ref in referenced:
                            if ref.getparent().tag == "ObjectPlacement":
                                find = True
                                break
                    if not find:
                        return error_msg
        else:
            identifier = entity.attrib["id"]
            referenced = self.tree.findall(f".//*[@ref='{identifier}']")
            if len(referenced) > 0:
                for ref in referenced:
                    if ref.getparent().tag == "ShapeOfProduct":
                        representation = ref.getparent().getparent()
                        representation_type = (
                            representation.attrib[self.type]
                            if self.type in representation.attrib
                            else representation.tag
                        )
                        if representation_type == "IfcShapeRepresentation":
                            if placement is None:
                                find = False
                                identifier = entity.attrib["id"]
                                referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                                if len(referenced) > 0:
                                    for ref2 in referenced:
                                        if ref2.getparent().tag == "ObjectPlacement":
                                            find = True
                                            break
                                if not find:
                                    return error_msg


    def PositiveLengthParameter(self, entity, ifcname, called_entity=None):
        """Checks if the parameter length has a value greater than zero.
        ----------
        This is used in IfcReparametrisedCompositeCurveSegment."""
        if float(entity.attrib["ParamLength"]) <= 0:
            return "The ParamLength shall be greater than zero"


    def PreDefinedColourNames(self, entity, ifcname, called_entity=None):
        """Checks if the color name is not in the predefined list.
        ----------
        This is used in IfcDraughtingPreDefinedColour."""
        names = ["black", "red", "green", "blue", "yellow", "magenta", "cyan", "white", "by layer"]
        if entity.attrib["Name"] not in names:
            return "The inherited name for pre defined items shall only have the value of one "\
                "of the words 'black', 'red', 'green', 'blue', 'yellow', 'magenta', 'cyan', "\
                "'white', 'by layer'"


    def PreDefinedCurveFontNames(self, entity, ifcname, called_entity=None):
        """Checks if the predefined curve font names are not in the allowed list.
        ----------
        This is used in IfcDraughtingPreDefinedCurveFont."""
        names = ["continuous", "chain", "chain double dash", "dashed", "dotted", "by layer"]
        if entity.attrib["Name"] not in names:
            return "The name of the IfcDraughtingPreDefinedCurveFont shall be 'continuous', "\
                "'chain', 'chain double dash', 'dashed', 'dotted' or 'by layer'"


    def ProjectedIsGlobal(self, entity, ifcname, called_entity=None):
        """Checks if a projected length is not assigned in local coordinate directions.
        ----------
        This is used in IfcStructuralCurveAction & IfcStructuralSurfaceAction."""
        if "ProjectedOrTrue" in entity.attrib:
            if (
                entity.attrib["ProjectedOrTrue"].lower() == "projected_length"
                and entity.attrib["GlobalOrLocal"].lower() != "global_coords"
            ):
                return "A load can only be related to projected length if it was specified "\
                    "in global coordinate directions (i.e. in analysis model coordinate "\
                    "directions). If a load was specified in local coordinate directions, "\
                    "it can only relate to true length"


    def RasterCodeByteStream(self, entity, ifcname, called_entity=None):
        """Checks if the size of the raster code is in bytesize (multiple of 8 bits).
        ----------
        This is used in IfcBlobTexture."""
        code = entity.attrib["RasterCode"]
        if len(str(code)) % 8 != 0:
            return "The size of the raster code shall be a multiple of 8 bits"


    def RefDirIs3D(self, entity, ifcname, called_entity=None):
        """Checks if the refdirection attribute references a 3D direction, if given.
        ----------
        This is used in IfcAxis2Placement3D."""
        refdir = entity.find("RefDirection")
        if refdir is not None:
            if "ref" in refdir.attrib:
                refdir = self.ref_check(refdir)
            if len(re.split(r"\s+", refdir.attrib["DirectionRatios"])) != 3:
                return "The RefDirection when given should only reference a three-dimensional "\
                    "IfcDirection"


    def RefHatchLine2D(self, entity, ifcname, called_entity=None):
        """Checks if the reference hatch line is 2D-
        ----------
        This is used in IfcFillAreaStyleHatching."""
        hatchline = entity.find("PointOfReferenceHatchLine")
        if hatchline is not None:
            if "ref" in hatchline.attrib:
                hatchline = self.ref_check(hatchline)
            if len(re.split(r"\s+", hatchline.attrib["Coordinates"])) != 2:
                return "The IfcCartesianPoint, if given as value to PointOfReferenceHatchLine "\
                    "shall have the dimensionality of 2"


    def RequiresEdgeCurve(self, entity, ifcname, called_entity=None):
        """Checks if the bounding edges are defined as edge curves.
        ----------
        This is used in IfcAdvancedFace."""
        bounds = entity.find("Bounds")
        error_msg = "The geometry of all bounding edges of the face shall be fully defined as "\
            "IfcEdgeCurve's"
        for b in bounds:
            bound = b.find("Bound")
            if "ref" in bound.attrib:
                bound = self.ref_check(bound)
            bound_type = bound.attrib[self.type] if self.type in bound.attrib else bound.tag
            if bound_type != "IfcEdgeLoop":
                return error_msg
            else:
                edges = bound.find("EdgeList")
                for edge in edges:
                    edge_elem = edge.find("EdgeElement")
                    if "ref" in edge_elem.attrib:
                        edge_elem = self.ref_check(edge_elem)
                    edge_elem = (
                        edge_elem.attrib[self.type]
                        if self.type in edge_elem.attrib
                        else edge_elem.tag
                    )
                    if edge_elem != "IfcEdgeCurve":
                        return error_msg


    def SameDim(self, entity, ifcname, called_entity=None):
        """Checks if all poins/segments/directions/etc. have the same dimension.
        ----------
        This is used in IfcBooleanResult, IfcBSplineCurve, IfcCompositeCurve, IfcLine
        & IfcPolyline."""
        if ifcname == "IfcBSplineCurve":
            bspline = entity.find("ControlPointsList")
            if "ref" in bspline[0].attrib:
                bspline[0] = self.ref_check(bspline[0])
            dim = len(re.split(r"\s+", str(bspline[0].attrib["Coordinates"])))
            for points in bspline:
                if "ref" in points.attrib:
                    points = self.ref_check(points)
                if len(re.split(r"\s+", str(points.attrib["Coordinates"]))) != dim:
                    return "All control points shall have the same dimensionality"
        elif ifcname == "IfcCompositeCurve":
            composite = (
                [entity.getparent().getparent()]
                if called_entity == "Segments"
                else entity.find("Segments")
            )
            if composite is None:
                composite = []
                identifier = entity.attrib["id"]
                referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                if len(referenced) > 0:
                    for ref in referenced:
                        if ref.getparent().tag == "UsingCurves":
                            composite.append(ref.getparent().getparent())

            if composite:
                if "ref" in composite[0].attrib:
                    composite[0] = self.ref_check(composite[0])
                cc = composite[0].find("ParentCurve")
                if "ref" in cc.attrib:
                    cc = self.ref_check(cc)
                ifccc = cc.attrib[self.type] if self.type in cc.attrib else cc.tag
                dim = self.IfcDimensionSize(cc, ifccc)
                for child in composite:
                    cc2 = child.find("ParentCurve")
                    if "ref" in cc2.attrib:
                        cc2 = self.ref_check(cc2)
                    ifccc2 = cc2.attrib[self.type] if self.type in cc2.attrib else cc2.tag
                    dim2 = self.IfcDimensionSize(cc2, ifccc2)
                    if dim != dim2:
                        return "All segments shall have the same dimensionality"

        elif ifcname == "IfcLine":
            point = entity.find("Pnt")
            if "ref" in point.attrib:
                point = self.ref_check(point)
            direction = entity.find("Dir")
            if "ref" in direction.attrib:
                direction = self.ref_check(direction)
            dir_orientation = entity.find("Orientation")
            if "ref" in dir_orientation.attrib:
                dir_orientation = self.ref_check(dir_orientation)
            if len(re.split(r"\s+", str(point.attrib["Coordinates"]))) != len(
                re.split(r"\s+", str(dir_orientation.attrib["DirectionRatios"]))
            ):
                return "The dimensionality of the Pnt and Dir shall be the same"
        elif ifcname == "IfcPolyline":
            polyline = entity.find("Points")
            if "ref" in polyline[0].attrib:
                polyline[0] = self.ref_check(polyline[0])
            dim = len(re.split(r"\s+", str(polyline[0].attrib["Coordinates"])))
            for points in polyline:
                if "ref" in points.attrib:
                    points = self.ref_check(points)
                if len(re.split(r"\s+", str(points.attrib["Coordinates"]))) != dim:
                    return "The space dimensionality of all Points shall be the same"
        elif ifcname == "IfcBooleanResult":
            #Always true since all entities of type IfcBooleanOperand have a dimension of 3.
            pass
        else:
            #curve type is unknown
            return "Curve type is unknown"


    def SameNumOfWeightsAndPoints(self, entity, ifcname, called_entity=None):
        """Checks if the number of weights and control points is equal.
        ----------
        This is used in IfcRationalBSplineCurveWithKnots."""
        cpl = len(re.split(r"\s+", str(entity.attrib["ControlPointsList"])))
        weights = len(re.split(r"\s+", str(entity.attrib["WeightsData"])))
        if cpl != weights:
            return "There shall be the same number of weights as control points"


    def SameSurface(self, entity, ifcname, called_entity=None):
        """Checks if associated surfaces are the same.
        ----------
        This is used in IfcCompositeCurveOnSurface & IfcSeamCurve."""
        if ifcname == "IfcCompositeCurveOnSurface":
            surfaces = self.IfcGetBasisSurface(entity)
            if len(surfaces) != 1:
                return "The BasisSurface shall contain at least one surface (and exactly one "\
                    "surface). This ensures that all segments reference curves on the same surface"
        elif ifcname == "IfcSeamCurve":
            geometry = entity.find("AssociatedGeometry")
            if "ref" in geometry.attrib:
                geometry = self.ref_check(geometry)
            if "ref" in geometry[0].attrib:
                geometry[0] = self.ref_check(geometry[0])
            if "ref" in geometry[1].attrib:
                geometry[1] = self.ref_check(geometry[1])
            equal = self.elements_equal(geometry[0], geometry[1])
            if not equal:
                return "The two associated geometries shall be related to the same surface"


    def SameUnitLowerSet(self, entity, ifcname, called_entity=None):
        """Checks if the measure type of the lower bound is the same as the set point measure.
        ----------
        This is used in IfcPropertyBoundedValue."""
        if "LowerBoundValue" in entity.attrib and "SetPointValue" in entity.attrib:
            if entity.attrib["LowerBoundValue"] != entity.attrib["SetPointValue"]:
                return "The measure type of the LowerBoundValue shall be the same as the measure "\
                    "type of the SetPointValue, if both (lower bound and set point) are given"


    def SameUnitUpperLower(self, entity, ifcname, called_entity=None):
        """Checks if the measure type of the lower bound is the same as the upper bound measure.
        ----------
        This is used in IfcPropertyBoundedValue."""
        if "UpperBoundValue" in entity.attrib and "LowerBoundValue" in entity.attrib:
            if entity.attrib["UpperBoundValue"] != entity.attrib["LowerBoundValue"]:
                return "The measure type of the UpperBoundValue shall be the same as the measure "\
                    "type of the LowerBoundValue, if both (upper and lower bound) are given"


    def SameUnitUpperSet(self, entity, ifcname, called_entity=None):
        """Checks if the measure type of the upper bound is the same as the set point measure.
        ----------
        This is used in IfcPropertyBoundedValue."""
        if "UpperBoundValue" in entity.attrib and "SetPointValue" in entity.attrib:
            if entity.attrib["UpperBoundValue"] != entity.attrib["SetPointValue"]:
                return "The measure type of the UpperBoundValue shall be the same as the measure "\
                    "type of the SetPointValue, if both (upper bound and set point) are given"


    def Scale2GreaterZero(self, entity, ifcname, called_entity=None):
        """Checks if the second scale is greater than 0. If not given, it is derived from the
        first scale, which default value is 1.0.
        ----------
        This is used in IfcCartesianTransformationOperator2DnonUniform
        & IfcCartesianTransformationOperator3DnonUniform."""
        if "Scale" not in entity.attrib or entity.attrib["Scale"] == "":
            scale = 1.0
        else:
            scale = float(entity.attrib["Scale"])

        if "Scale2" not in entity.attrib or entity.attrib["Scale2"] == "":
            scale2 = scale
        else:
            scale2 = float(entity.attrib["Scale2"])

        if scale2 <= 0:
            return "The derived scaling Scale2 shall be greater than zero"


    def Scale3GreaterZero(self, entity, ifcname, called_entity=None):
        """Checks if the third scale is greater than 0. If not given, it is derived from the
        first scale, which default value is 1.0.
        ----------
        This is used in IfcCartesianTransformationOperator3DnonUniform."""
        if "Scale" not in entity.attrib or entity.attrib["Scale"] == "":
            scale = 1.0
        else:
            scale = float(entity.attrib["Scale"])

        if "Scale3" not in entity.attrib or entity.attrib["Scale3"] == "":
            scale3 = scale
        else:
            scale3 = float(entity.attrib["Scale3"])

        if scale3 <= 0:
            return "The derived scaling Scale3 shall be greater than zero"


    def ScaleGreaterZero(self, entity, ifcname, called_entity=None):
        """Checks if the scale is greater than 0. If not given, the default value is 1.0.
        ----------
        This is used in IfcCartesianTransformationOperator."""
        if "Scale" not in entity.attrib or entity.attrib["Scale"] == "":
            scale = 1.0
        else:
            scale = float(entity.attrib["Scale"])

        if scale <= 0:
            return "The derived scaling Scale shall be greater than zero"


    def SecondOperandClosed(self, entity, ifcname, called_entity=None):
        """Checks if the second operand is a closed tessellation, if it is a tessellated face set.
        ----------
        This is used in IfcBooleanResult."""
        second_op = entity.find("SecondOperand")[0]
        if second_op.tag == "IfcTriangulatedFaceSet" or second_op.tag == "IfcPolygonalFaceSet":
            if "ref" in second_op.attrib:
                second_op = self.ref_check(second_op)
            if second_op.attrib["Closed"].lower() != "true":
                return "If the SecondOperand is of type IfcTessellatedFaceSet it has to be a "\
                    "closed tessellation"


    def SecondOperandType(self, entity, ifcname, called_entity=None):
        """Checks if the second operand of the boolean clipping operation is a half space solid.
        ----------
        This is used in IfcBooleanClippingResult."""
        allowed_types = ["IfcHalfSpaceSolid"]
        second_op = entity.find("SecondOperand")[0]
        if not self.attr_list_check(second_op.tag, allowed_types):
            return "The second operand of the Boolean clipping operation shall be an "\
                "IfcHalfSpaceSolid"


    def SizeOfPixelList(self, entity, ifcname, called_entity=None):
        """Checks if pixel list has the correct size.
        ----------
        This is used in IfcPixelTexture."""
        width = int(entity.attrib["Width"])
        height = int(entity.attrib["Height"])
        if len(re.split(r"\s+", entity.attrib["Pixel"])) != width * height:
            return "The list of pixel shall have exactly width*height members"


    def SpineCurveDim(self, entity, ifcname, called_entity=None):
        """Checks if the spine curve is 3D.
        ----------
        This is used in IfcSectionedSpine."""
        curve = entity.find("SpineCurve")
        if "ref" in curve.attrib:
            curve = self.ref_check(curve)
        curve_type = curve.attrib[self.type] if self.type in curve.attrib else curve.tag
        dim = self.IfcDimensionSize(curve, curve_type)
        if dim != 3:
            return "The curve entity which is the underlying spine curve shall have the "\
                "dimensionality of 3"


    def SuitableLoadType(self, entity, ifcname, called_entity=None):
        """Checks if the load type is suitable for the current entity.
        ----------
        This is used in IfcStructuralLinearAction, IfcStructuralPlanarAction,
        IfcStructuralPointAction & IfcStructuralPointReaction."""
        if ifcname == "IfcStructuralLinearAction":
            allowed = ["IfcStructuralLoadLinearForce", "IfcStructuralLoadTemperature"]
            loadtype = entity.find("AppliedLoad")
            if "ref" in loadtype.attrib:
                loadtype = self.ref_check(loadtype)
            loadtype = loadtype.attrib[self.type] if self.type in loadtype.attrib else loadtype.tag
            if not self.attr_list_check(loadtype, allowed):
                return "A linear action shall place either a linear force or a temperature load"
        elif ifcname == "IfcStructuralPlanarAction":
            allowed = ["IfcStructuralLoadPlanarForce", "IfcStructuralLoadTemperature"]
            loadtype = entity.find("AppliedLoad")
            if "ref" in loadtype.attrib:
                loadtype = self.ref_check(loadtype)
            loadtype = loadtype.attrib[self.type] if self.type in loadtype.attrib else loadtype.tag
            if not self.attr_list_check(loadtype, allowed):
                return "A planar action shall place either a planar force or a temperature load"
        elif ifcname in ("IfcStructuralPointAction", "IfcStructuralPointReaction"):
            allowed = ["IfcStructuralLoadSingleForce", "IfcStructuralLoadSingleDisplacement"]
            loadtype = entity.find("AppliedLoad")
            if "ref" in loadtype.attrib:
                loadtype = self.ref_check(loadtype)
            loadtype = loadtype.attrib[self.type] if self.type in loadtype.attrib else loadtype.tag
            if not self.attr_list_check(loadtype, allowed):
                return "A structural point action shall place either a single force or a single "\
                    "displacement"


    def SuitablePredefinedType(self, entity, ifcname, called_entity=None):
        """Checks if the predefined type is suitable for the current entity.
        ----------
        This is used in IfcStructuralCurveAction & IfcStructuralCurveReaction."""
        if ifcname == "IfcStructuralCurveAction":
            predefined = entity.attrib["PredefinedType"].lower()
            if predefined == "equidistant":
                return "The EQUIDISTANT distribution type is out of scope of structural "\
                    "curve actions"
        elif ifcname == "IfcStructuralCurveReaction":
            predefined = entity.attrib["PredefinedType"].lower()
            if predefined in ("sinus", "parabola"):
                return "The SINUS and PARABOLA distribution types are out of scope of structural "\
                    "curve reactions"


    def SupportedRasterFormat(self, entity, ifcname, called_entity=None):
        """Checks if the raster data format is supported.
        ----------
        This is used in IfcBlobTexture."""
        allowed_formats = ["bmp", "jpg", "gif", "png"]
        if entity.attrib["RasterFormat"].lower() not in allowed_formats:
            return "Currently the formats of bmp, jpg, gif and png, shall be supported"


    def SurfaceAndOrShearAreaSpecified(self, entity, ifcname, called_entity=None):
        """Checks if the surface area or the shear are is specified (or both).
        ----------
        This is used in IfcSurfaceReinforcementArea."""
        if (
            (
                "SurfaceReinforcement1" not in entity.attrib
                or entity.attrib["SurfaceReinforcement1"] == ""
            )
            and (
                "SurfaceReinforcement2" not in entity.attrib
                or entity.attrib["SurfaceReinforcement2"] == ""
            )
            and (
                "ShearReinforcement" not in entity.attrib
                or entity.attrib["ShearReinforcement"] == ""
            )
        ):
            return "At least one of the reinforcement area attributes shall be specified"


    def SweptAreaType(self, entity, ifcname, called_entity=None):
        """Checks if the profile type for the swept area is 'area'.
        ----------
        This is used in IfcSweptAreaSolid."""
        area = entity.find("SweptArea")
        if "ref" in area.attrib:
            area = self.ref_check(area)
        area = area.attrib["ProfileType"].lower()
        if area != "area":
            return "The profile definition for the swept area solid shall be of type AREA"


    def Trim1ValuesConsistent(self, entity, ifcname, called_entity=None):
        """Checks if the trim values have a different type, if multiple are given.
        ----------
        This is used in IfcTrimmedCurve."""
        trim = entity.find("Trim1")
        if "ref" in trim.attrib:
            trim = self.ref_check(trim)
        if len(trim) == 2:
            allowed_types = ["IfcCartesianPoint", "IfcParameterValue"]
            trim_val1 = trim[0].tag
            if "-wrapper" in trim_val1:
                trim_val1 = re.sub("-wrapper", "", trim_val1)
            if trim_val1 not in allowed_types:
                trim_val1 = list(
                    set(self.entities[trim_val1]["supertypes"]).intersection(set(allowed_types))
                )[0]
            trim_val2 = trim[1].tag
            if "-wrapper" in trim_val1:
                trim_val2 = re.sub("-wrapper", "", trim_val2)
            if trim_val2 not in allowed_types:
                trim_val2 = list(
                    set(self.entities[trim_val2]["supertypes"]).intersection(set(allowed_types))
                )[0]
            if trim_val1 == trim_val2:
                return "Either a single value is specified for Trim1, or the two trimming values "\
                    "are of different type (point and parameter)"


    def Trim2ValuesConsistent(self, entity, ifcname, called_entity=None):
        """Checks if the trim values have a different type, if multiple are given.
        ----------
        This is used in IfcTrimmedCurve."""
        trim = entity.find("Trim2")
        if "ref" in trim.attrib:
            trim = self.ref_check(trim)
        if len(trim) == 2:
            allowed_types = ["IfcCartesianPoint", "IfcParameterValue"]
            trim_val1 = trim[0].tag
            if "-wrapper" in trim_val1:
                trim_val1 = re.sub("-wrapper", "", trim_val1)
            if trim_val1 not in allowed_types:
                trim_val1 = list(
                    set(self.entities[trim_val1]["supertypes"]).intersection(set(allowed_types))
                )[0]
            trim_val2 = trim[1].tag
            if "-wrapper" in trim_val1:
                trim_val2 = re.sub("-wrapper", "", trim_val2)
            if trim_val2 not in allowed_types:
                trim_val2 = list(
                    set(self.entities[trim_val2]["supertypes"]).intersection(set(allowed_types))
                )[0]
            if trim_val1 == trim_val2:
                return "Either a single value is specified for Trim2, or the two trimming values "\
                    "are of different type (point and parameter)"


    def TwoPCurves(self, entity, ifcname, called_entity=None):
        """Checks if the intersection curve has two associated geometry elements.
        ----------
        This is used in IfcIntersectionCurve & IfcSeamCurve."""
        geometry = entity.find("AssociatedGeometry")
        if len(geometry) != 2:
            return "The intersection curve shall have precisely two associated geometry elements"


    def U1AndU2Different(self, entity, ifcname, called_entity=None):
        """Checks if U1 and U2 have different values.
        ----------
        This is used in IfcRectangularTrimmedSurface."""
        u1 = entity.attrib["U1"]
        u2 = entity.attrib["U2"]
        if u1 == u2:
            return "U1 and U2 shall have different values"


    def UDirectionConstraints(self, entity, ifcname, called_entity=None):
        """Checks if U-direction constraints are valid.
        ----------
        This is used in IfcBSplineSurfaceWithKnots."""
        degree = int(entity.attrib["UDegree"])
        multiplicities = re.split(r"\s+", entity.attrib["UMultiplicities"])
        knots = re.split(r"\s+", entity.attrib["UKnots"])
        #conditions = self.IfcConstraintsParamBSpline(degree, upper, multiplicities, knots)
        points = len(entity.find("ControlPointsList"))
        sol1 = []
        sol2 = []
        x = 1
        while True:
            y = x
            while True:
                sol = x * y
                if sol > points:
                    break
                elif sol == points:
                    sol1.append(x)
                    sol2.append(y)
                    break
                else:
                    y = y + 1
            if x == y:
                break
            x = x + 1

        possible_upper = set(sol1).union(set(sol2))
        result = False
        for upper in possible_upper:
            conditions = self.IfcConstraintsParamBSpline(degree, upper - 1, multiplicities, knots)
            if conditions:
                result = True
                break
        if not result:
            return "The function returns TRUE when the parameter constraints are verified for "\
                "the u direction"


    def UnboundedSurface(self, entity, ifcname, called_entity=None):
        """Checks if the base surface is not a bounded one.
        ----------
        This is used in IfcBoxedHalfSpace."""
        surface = entity.find("BaseSurface")
        if "ref" in surface.attrib:
            surface = self.ref_check(surface)
        surface = surface.attrib[self.type] if self.type in surface.attrib else surface.tag
        if self.attr_check(surface, "IfcBoundedSurface"):
            return "The BaseSurface defining the half space shall not be a bounded surface"


    def UniquePropertyNames(self, entity, ifcname, called_entity=None):
        """Checks if the property names are unique.
        ----------
        Each property of the corresponding lists need to have a unique name value within
        that list."""
        #This is used in IfcComplexPropertyTemplate, IfcPropertySet & IfcPropertySetTemplate.
        unique_list = []
        if ifcname == "IfcPropertySet":
            properties = entity.find("HasProperties")
        else:
            properties = entity.find("HasPropertyTemplates")

        if properties is None:
            if ifcname == "IfcPropertySet":
                called_tag = "PartOfPset"
            elif ifcname == "IfcPropertySetTemplate":
                called_tag = "PartOfPsetTemplate"
            elif ifcname == "IfcComplexPropertyTemplate":
                called_tag = "PartOfComplexTemplate"
            properties = []
            identifier = entity.attrib["id"]
            referenced = self.tree.findall(f".//*[@ref='{identifier}']")
            if len(referenced) > 0:
                for ref in referenced:
                    if ref.getparent().tag == called_tag:
                        properties.append(ref.getparent().getparent())

            if called_entity in ("HasProperties", "HasPropertyTemplates"):
                properties.append(entity.getparent().getparent())

        for prop in properties:
            if "ref" in prop.attrib:
                prop = self.ref_check(prop)
            if prop.attrib["Name"] in unique_list:
                return "Not all properties within the property list have unique names"
            else:
                unique_list.append(prop.attrib["Name"])


    def UniquePropertySetNames(self, entity, ifcname, called_entity=None):
        """Checks if the property set names are unique.
        ----------
        This is used in IfcTypeObject."""
        unique_list = []
        properties = entity.find("HasPropertySets")
        if properties is None:
            properties = []
            identifier = entity.attrib["id"]
            referenced = self.tree.findall(f".//*[@ref='{identifier}']")
            if len(referenced) > 0:
                for ref in referenced:
                    if ref.getparent().tag == "DefinesType":
                        properties.append(ref.getparent().getparent())

            if called_entity == "HasPropertySets":
                properties.append(entity.getparent().getparent())

        for prop in properties:
            if "ref" in prop.attrib:
                prop = self.ref_check(prop)
            if prop.attrib["Name"] in unique_list:
                return "Not all properties within the property set sets have unique names"
            else:
                unique_list.append(prop.attrib["Name"])


    def UniqueQuantityNames(self, entity, ifcname, called_entity=None):
        """Checks if the quantity names are unique.
        ----------
        This is used in IfcElementQuantity & IfcPhysicalComplexQuantity."""
        unique_list = []
        if ifcname == "IfcElementQuantity":
            quantities = entity.find("Quantities")
        else:
            quantities = entity.find("HasQuantities")

        if quantities is None and ifcname == "IfcPhysicalComplexQuantity":
            quantities = []
            identifier = entity.attrib["id"]
            referenced = self.tree.findall(f".//*[@ref='{identifier}']")
            if len(referenced) > 0:
                for ref in referenced:
                    if ref.tag == "PartOfComplex":
                        quantities.append(ref.getparent())

            if called_entity == "HasQuantities":
                quantities.append(entity.getparent().getparent())

        if quantities:
            for q in quantities:
                if "ref" in q.attrib:
                    q = self.ref_check(q)
                if q.attrib["Name"] in unique_list:
                    return "Not all quantities within the quantity set have unique names"
                else:
                    unique_list.append(q.attrib["Name"])


    def UsenseCompatible(self, entity, ifcname, called_entity=None):
        """Checks if the direction Usense is compatible with the ordered parameter values for U.
        ----------
        This is used in IfcRectangularTrimmedSurface."""
        u1 = entity.attrib["U1"]
        u2 = entity.attrib["U2"]
        usense = BoolConv(entity.attrib["Usense"])
        surface = entity.find("BasisSurface")
        if "ref" in surface.attrib:
            surface = self.ref_check(surface)
        surface = surface.attrib[self.type] if self.type in surface.attrib else surface.tag

        if surface == "IfcPlane":
            test1 = False
        else:
            test1 = self.attr_check(surface, "IfcElementarySurface")
        test2 = bool(surface == "IfcSurfaceOfRevolution")
        if float(u2) > float(u1):
            test3 = bool(usense)
        else:
            test3 = not bool(usense)

        if not (test1 or test2 or test3):
            return "With exception of those surfaces closed in the U parameter, direction Usense "\
                "shall be compatible with the ordered parameter values for U"


    def UserTargetProvided(self, entity, ifcname, called_entity=None):
        """Checks if a userdefined target view is given, if target view is set to 'userdefined'.
        ----------
        This is used in IfcGeometricRepresentationSubContext."""
        if entity.attrib["TargetView"].lower() == "userdefined":
            if not (
                "UserDefinedTargetView" in entity.attrib
                and entity.attrib["UserDefinedTargetView"] != ""
            ):
                return "The attribute UserDefinedTargetView shall be given, if the attribute "\
                    "TargetView is set to USERDEFINED"


    def V1AndV2Different(self, entity, ifcname, called_entity=None):
        """Checks if V1 and V2 are not equal.
        ----------
        This is used in IfcRectangularTrimmedSurface."""
        v1 = entity.attrib["V1"]
        v2 = entity.attrib["V2"]
        if v1 == v2:
            return "V1 and V2 shall have different values"


    def VDirectionConstraints(self, entity, ifcname, called_entity=None):
        """Checks if V-direction constraints are valid.
        ----------
        This is used in IfcBSplineSurfaceWithKnots."""
        degree = int(entity.attrib["VDegree"])
        multiplicities = re.split(r"\s+", entity.attrib["VMultiplicities"])
        knots = re.split(r"\s+", entity.attrib["VKnots"])
        points = len(entity.find("ControlPointsList"))
        sol1 = []
        sol2 = []
        x = 1
        while True:
            y = x
            while True:
                sol = x * y
                if sol > points:
                    break
                elif sol == points:
                    sol1.append(x)
                    sol2.append(y)
                    break
                else:
                    y = y + 1
            if x == y:
                break
            x = x + 1

        possible_upper = set(sol1).union(set(sol2))
        result = False
        for upper in possible_upper:
            conditions = self.IfcConstraintsParamBSpline(degree, upper - 1, multiplicities, knots)
            result = bool(conditions)
            if result:
                break
        if not result:
            return "The function returns TRUE when the parameter constraints are verified for "\
                "the v direction"


    def ValidBottomFilletRadius(self, entity, ifcname, called_entity=None):
        """Checks if the bottom fillet radius is within the range of allowed values.
        ----------
        This is used in IfcAsymmetricIShapeProfileDef."""
        if (
            "BottomFlangeFilletRadius" in entity.attrib
            and entity.attrib["BottomFlangeFilletRadius"] != ""
        ):
            radius = float(entity.attrib["BottomFlangeFilletRadius"])
            width = float(entity.attrib["BottomFlangeWidth"])
            thickness = float(entity.attrib["WebThickness"])
            if radius > (width - thickness) / 2:
                return "The bottom fillet radius, if given, shall be within the range of "\
                    "allowed values"


    def ValidExtrusionDirection(self, entity, ifcname, called_entity=None):
        """Checks if the extruded direction is not perpendicular to the local z-axis.
        ----------
        This is used in IfcExtrudedAreaSolid."""
        extruded = entity.find("ExtrudedDirection")
        if "ref" in extruded.attrib:
            extruded = self.ref_check(extruded)
        direction = re.split(r"\s+", extruded.attrib["DirectionRatios"])
        direction = self.IfcNormalise(direction)
        z_vector = [0.0, 0.0, 1.0]
        scalar = 0.0
        for i, direct in enumerate(direction):
            scalar = scalar + z_vector[i] * direct
        if scalar == 0:
            return "The ExtrudedDirection shall not be perpendicular to the local z-axis"


    def ValidFilletRadius(self, entity, ifcname, called_entity=None):
        """Checks if the fillet radius is within the range of allowed values.
        ----------
        This is used in IfcIShapeProfileDef."""
        if "FilletRadius" in entity.attrib and entity.attrib["FilletRadius"] != "":
            radius = float(entity.attrib["FilletRadius"])
            width = float(entity.attrib["OverallWidth"])
            web_thickness = float(entity.attrib["WebThickness"])
            depth = float(entity.attrib["OverallDepth"])
            flange_thickness = float(entity.attrib["FlangeThickness"])
            if (
                radius > (width - web_thickness) / 2
                or radius > (depth - (2 * flange_thickness)) / 2
            ):
                return "The FilletRadius, if given, shall be within the range of allowed values"


    def ValidFlangeThickness(self, entity, ifcname, called_entity=None):
        """Checks if the flange thickness value is within the range of allowed values.
        ----------
        This is used in IfcAsymmetricIShapeProfileDef, IfcIShapeProfileDef, IfcTShapeProfileDef,
        IfcUShapeProfileDef & IfcZShapeProfileDef."""
        if ifcname == "IfcAsymmetricIShapeProfileDef":
            if "TopFlangeThickness" in entity.attrib and entity.attrib["TopFlangeThickness"] != "":
                bottom_thickness = float(entity.attrib["BottomFlangeThickness"])
                top_thickness = float(entity.attrib["TopFlangeThickness"])
                depth = float(entity.attrib["OverallDepth"])
                if bottom_thickness + top_thickness >= depth:
                    return "The sum of flange thicknesses shall be less than the overall depth"
        elif ifcname == "IfcIShapeProfileDef":
            thickness = float(entity.attrib["FlangeThickness"])
            depth = float(entity.attrib["OverallDepth"])
            if (2 * thickness) >= depth:
                return "The sum of flange thicknesses shall be less than the overall depth"
        elif ifcname == "IfcTShapeProfileDef":
            thickness = float(entity.attrib["FlangeThickness"])
            depth = float(entity.attrib["Depth"])
            if thickness >= depth:
                return "The flange thickness shall be smaller than the depth"
        elif ifcname in ("IfcUShapeProfileDef", "IfcZShapeProfileDef"):
            thickness = float(entity.attrib["FlangeThickness"])
            depth = float(entity.attrib["Depth"])
            if thickness >= depth / 2:
                return "The flange thickness shall be smaller than half of the depth"


    def ValidGirth(self, entity, ifcname, called_entity=None):
        """Checks if the girth is smaller than half of the depth size.
        ----------
        This is used in IfcCShapeProfileDef."""
        girth = float(entity.attrib["Girth"])
        depth = float(entity.attrib["Depth"])
        if girth >= depth / 2:
            return "The girth shall be smaller than half of the depth"


    def ValidInnerRadius(self, entity, ifcname, called_entity=None):
        """Checks if inner fillet radius is small enough to fit into the void.
        ----------
        This is used in IfcRectangleHollowProfileDef."""
        if "InnerFilletRadius" in entity.attrib and entity.attrib["InnerFilletRadius"] != "":
            radius = float(entity.attrib["InnerFilletRadius"])
            thickness = float(entity.attrib["WallThickness"])
            xdim = float(entity.attrib["XDim"])
            ydim = float(entity.attrib["YDim"])
            if radius > (xdim / 2 - thickness) or radius > (ydim / 2 - thickness):
                return "The inner fillet radius (if given) shall be small enough to fit into "\
                    "the void"


    def ValidInternalFilletRadius(self, entity, ifcname, called_entity=None):
        """Checks if the internal fillet radius is small enough to fit into the inner space.
        ----------
        This is used in IfcCShapeProfileDef."""
        if "InternalFilletRadius" in entity.attrib and entity.attrib["InternalFilletRadius"] != "":
            radius = float(entity.attrib["InternalFilletRadius"])
            width = float(entity.attrib["Width"])
            depth = float(entity.attrib["Depth"])
            thickness = float(entity.attrib["WallThickness"])
            if radius > (width / 2 - thickness) or radius > (depth / 2 - thickness):
                return "If the value for InternalFilletRadius is given, it shall be small enough "\
                    "to fit into the inner space"


    def ValidListSize(self, entity, ifcname, called_entity=None):
        """Checks if the amount of location items and value items is equal.
        ----------
        This is used in IfcStructuralLoadConfiguration."""
        values = entity.find("Values")
        locations = entity.find("Locations")
        if locations is not None:
            if len(values) != len(locations):
                return "If locations are provided, there shall be as many location items as "\
                    "there are value items"


    def ValidOuterRadius(self, entity, ifcname, called_entity=None):
        """Checks if the outer fillet radius is small enough to fit into the bounding box.
        ----------
        This is used in IfcRectangleHollowProfileDef."""
        if "OuterFilletRadius" in entity.attrib and entity.attrib["OuterFilletRadius"] != "":
            radius = float(entity.attrib["OuterFilletRadius"])
            xdim = float(entity.attrib["XDim"])
            ydim = float(entity.attrib["YDim"])
            if radius > xdim / 2 or radius > ydim / 2:
                return "The outer fillet radius (if given) shall be small enough to fit into "\
                    "the bounding box"


    def ValidRadius(self, entity, ifcname, called_entity=None):
        """Checks if the rounding radius is within the range of allowed values.
        ----------
        This is used in IfcRoundedRectangleProfileDef."""
        radius = float(entity.attrib["RoundingRadius"])
        xdim = float(entity.attrib["XDim"])
        ydim = float(entity.attrib["YDim"])
        if radius > xdim / 2 or radius > ydim / 2:
            return "The value of the attribute RoundingRadius shall be lower or equal than "\
                "either of both, half the value of the Xdim and the YDim attribute"


    def ValidSetOfNames(self, entity, ifcname, called_entity=None):
        """Checks if the family and/or given name is provided, if a middle name is provided.
        ----------
        This is used in IfcPerson."""
        if not (
            ("FamilyName" in entity.attrib and entity.attrib["FamilyName"] != "")
            or ("GivenName" in entity.attrib and entity.attrib["GivenName"] != "")
        ):
            if "MiddleNames" in entity.attrib and entity.attrib["MiddleNames"] != "":
                return "If middle names are provided, the family name or/ and the given name "\
                    "shall be provided too"


    def ValidThickness(self, entity, ifcname, called_entity=None):
        """Checks if the thickness is smaller than the depth and with.
        ----------
        This is used in IfcLShapeProfileDef."""
        thickness = float(entity.attrib["Thickness"])
        depth = float(entity.attrib["Depth"])
        if thickness >= depth:
            return "The thickness shall be smaller than the depth and width"
        else:
            if "Width" in entity.attrib and entity.attrib["Width"] != "":
                width = float(entity.attrib["Width"])

                if thickness >= width:
                    return "The thickness shall be smaller than the depth and width"


    def ValidTopFilletRadius(self, entity, ifcname, called_entity=None):
        """Checks if the top fillet radius is within the range of allowed values.
        ----------
        This is used in IfcAsymmetricShapeProfileDef."""
        if (
            "TopFlangeFilletRadius" in entity.attrib
            and entity.attrib["TopFlangeFilletRadius"] != ""
        ):
            radius = float(entity.attrib["TopFlangeFilletRadius"])
            width = float(entity.attrib["TopFlangeWidth"])
            thickness = float(entity.attrib["WebThickness"])
            if radius > (width - thickness) / 2:
                return "The top fillet radius, if given, shall be within the range of "\
                    "allowed values"


    def ValidWallThickness(self, entity, ifcname, called_entity=None):
        """Checks if the wall thickness is within the range of allowed values.
        ----------
        This is used in IfcCShapeProfileDef & IfcRectangleHollowProfileDef."""
        if ifcname == "IfcCShapeProfileDef":
            width = float(entity.attrib["Width"])
            depth = float(entity.attrib["Depth"])
            thickness = float(entity.attrib["WallThickness"])
            if thickness >= width / 2 or thickness >= depth / 2:
                return "The WallThickness shall be smaller than half of the Width and half of "\
                    "the Depth"
        elif ifcname == "IfcRectangleHollowProfileDef":
            thickness = float(entity.attrib["WallThickness"])
            xdim = float(entity.attrib["XDim"])
            ydim = float(entity.attrib["YDim"])
            if thickness >= xdim / 2 or thickness >= ydim / 2:
                return "The wall thickness shall be smaller than half of the X and Y dimension "\
                    "of the rectangle"


    def ValidWebThickness(self, entity, ifcname, called_entity=None):
        """Checks if the web thickness is smaller than the flange(s) width.
        ----------
        This is used in IfcAsymmetricIShapeProfileDef, IfcIShapeProfileDef, IfcTShapeProfileDef
        & IfcUShapeProfileDef."""
        if ifcname == "IfcAsymmetricIShapeProfileDef":
            bottom_width = float(entity.attrib["BottomFlangeWidth"])
            top_width = float(entity.attrib["TopFlangeWidth"])
            thickness = float(entity.attrib["WebThickness"])
            if thickness >= bottom_width or thickness >= top_width:
                return "The web thickness shall be less than either flange width"
        elif ifcname == "IfcIShapeProfileDef":
            width = float(entity.attrib["OverallWidth"])
            thickness = float(entity.attrib["WebThickness"])
            if thickness >= width:
                return "The web thickness shall be less than the flange width"
        elif ifcname in ("IfcTShapeProfileDef", "IfcUShapeProfileDef"):
            width = float(entity.attrib["FlangeWidth"])
            thickness = float(entity.attrib["WebThickness"])
            if thickness >= width:
                return "The web thickness shall be smaller than the flange width"


    def VisibleLengthGreaterEqualZero(self, entity, ifcname, called_entity=None):
        """Checks if the visible segment length is not negative.
        ----------
        This is used in IfcCurveStyleFontPattern."""
        length = float(entity.attrib["VisibleSegmentLength"])
        if length < 0:
            return "The value of a visible pattern length shall be equal or greater then zero"


    def VoidsHaveAdvancedFaces(self, entity, ifcname, called_entity=None):
        """Checks if each void within an advanced B-rep is an advanced face.
        ----------
        This is used in IfcAdvancedBrepWithVoids."""
        voids = entity.find("Voids")
        for void in voids:
            if "ref" in void.attrib:
                void = self.ref_check(void)
            faces = void.find("CfsFaces")
            for face in faces:
                if not self.attr_check(face.tag, "IfcAdvancedFace"):
                    return "Each face of the voids within the advanced B-rep with voids shall "\
                        "be of type IfcAdvancedFace"


    def VsenseCompatible(self, entity, ifcname, called_entity=None):
        """Checks if the Vsense values are compatible with the ordered parameter values for V.
        ----------
        This is used in IfcRectangularTrimmedSurface."""
        v1 = entity.attrib["V1"]
        v2 = entity.attrib["V2"]
        vsense = BoolConv(entity.attrib["Vsense"])
        if float(v2) > float(v1):
            if not vsense:
                return "Vsense shall be compatible with the ordered parameter values for V"
        else:
            if vsense:
                return "Vsense shall be compatible with the ordered parameter values for V"


    def WR01(self, entity, ifcname, called_entity=None):
        """Checks different types of rules. More informations are found in the documentation.
        ----------
        This is used in IfcUnitAssignment & IfcPropertyEnumeration."""
        if ifcname == "IfcUnitAssignment":
            units = entity.find("Units")
            named_number = 0
            derived_number = 0
            monetary_number = 0
            named_set = set()
            derived_set = set()
            for unit in units:
                if (
                    self.attr_check(unit.tag, "IfcNamedUnit-wrapper")
                    and unit.attrib["UnitType"].lower() != "userdefined"
                ):
                    named_number += 1
                    named_set.add(unit.attrib["UnitType"].lower())
                elif (
                    self.attr_check(unit.tag, "IfcDerivedUnit-wrapper")
                    and unit.attrib["UnitType"].lower() != "userdefined"
                ):
                    derived_number += 1
                    derived_set.add(unit.attrib["UnitType"].lower())
                elif self.attr_check(unit.tag, "IfcMonetaryUnit-wrapper"):
                    monetary_number += 1
            if not (
                len(named_set) == named_number
                and len(derived_set) == derived_number
                and monetary_number <= 1
            ):
                return "Checks that the set of globally assigned units has each unit type "\
                    "(either of type IfcNamedUnit, IfcDerivedUnit, or IfcMonetaryUnit) "\
                    "defined only once"
        elif ifcname == "IfcPropertyEnumeration":
            values = entity.find("EnumerationValues")
            value_type = values[0].tag
            for value in values:
                if value.tag != value_type:
                    return "All values within the list of EnumerationValues shall be of the "\
                        "same measure type"


    def WR1(self, entity, ifcname, called_entity=None):
        """Checks different types of rules. More informations are found in the documentation.
        ----------
        This is used in IfcProxy, IfcRelAssigns, IfcZone, IfcActorRole, IfcAddress,
        IfcPostalAddress, IfcDocumentReference, IfcExternalReference, IfcGridAxis, IfcDerivedUnit,
        IfcNamedUnit, IfcArbitraryClosedProfileDef, IfcAbitraryProfileDefWithVoids,
        IfcCircleHollowProfileDef & IfcTable."""
        if ifcname == "IfcProxy":
            if "Name" not in entity.attrib or entity.attrib["Name"] == "":
                return "The Name attribute has to be provided for a proxy"
        elif ifcname == "IfcRelAssigns":
            if "RelatedObjectsType" in entity.attrib and entity.attrib["RelatedObjectsType"] != "":
                obj_type = entity.attrib["RelatedObjectsType"]
                if called_entity != "RelatedObjects":
                    objects = entity.find("RelatedObjects")
                else:
                    objects = []
                    objects.append(entity.getparent().getparent())
                    identifier = entity.attrib["id"]
                    referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                    if len(referenced) > 0:
                        for ref in referenced:
                            if ref.getparent().tag == "HasAssignments":
                                objects.append(ref.getparent().getparent())
                result = self.IfcCorrectObjectAssignment(obj_type, objects)
                if not result:
                    return "Rule checks whether the types of the assigned related objects comply "\
                        "with the contraint given by the RelatedObjectsType. The rule is "\
                        "important for constraint checks at subtypes of IfcRelAssigns or at "\
                        "subtypes of IfcObject, which refers to assignment relationships through "\
                        "the inverse HasAssignments relation"
                elif result == "?":
                    return "Not possible to check the proper use of RelatedObjects according to "\
                        "the RelatedObjectsType, since the RelatedObjectsType is unknown"
        elif ifcname == "IfcZone":
            groups = entity.find("IsGroupedBy")
            if groups is not None:
                for group in groups:
                    if "ref" in group.attrib:
                        group = self.ref_check(group)
                    allowed = ["IfcZone", "IfcSpace", "IfcSpatialZone"]
                    related_objects = group.find("RelatedObjects")
                    for obj in related_objects:
                        if obj.tag not in allowed:
                            return "An IfcZone is grouped by the objectified relationship "\
                                "IfcRelAssignsToGroup. Only objects of type IfcSpace, IfcZone "\
                                "and IfcSpatialZone are allowed as RelatedObjects"
        elif ifcname == "IfcActorRole":
            if entity.attrib["Role"].lower() == "userdefined":
                if "UserDefinedRole" not in entity.attrib or entity.attrib["UserDefinedRole"] == "":
                    return "If the attribute Role has the enumeration value USERDEFINED then a "\
                        "value for the attribute UserDefinedRole shall be asserted"
        elif ifcname == "IfcAddress":
            if "Purpose" in entity.attrib and entity.attrib["Purpose"].lower() == "userdefined":
                if (
                    "UserDefinedPurpose" not in entity.attrib
                    or entity.attrib["UserDefinedPurpose"] == ""
                ):
                    return "Either attribute value Purpose is not given, or when attribute "\
                        "Purpose has enumeration value USERDEFINED then attribute "\
                        "UserDefinedPurpose shall also have a value"
        elif ifcname == "IfcPostalAddress":
            if not (
                ("InternalLocation" in entity.attrib and entity.attrib["InternalLocation"] != "")
                or ("AddressLines" in entity.attrib and entity.attrib["AddressLines"] != "")
                or ("PostalBox" in entity.attrib and entity.attrib["PostalBox"] != "")
                or ("PostalCode" in entity.attrib and entity.attrib["PostalCode"] != "")
                or ("Town" in entity.attrib and entity.attrib["Town"] != "")
                or ("Region" in entity.attrib and entity.attrib["Region"] != "")
                or ("Country" in entity.attrib and entity.attrib["Country"] != "")
            ):
                return "Requires that at least one attribute of internal location, address "\
                    "lines, town, region or country is asserted. It is not acceptable to have "\
                    "a postal address without at least one of these values"
        elif ifcname == "IfcDocumentReference":
            document = (
                entity.getparent().getparent()
                if called_entity == "ReferencedDocument"
                else entity.find("ReferencedDocument")
            )
            error_msg = "A name should only be given, if no document information (including the "\
                "document name) is attached"
            if "Name" in entity.attrib and entity.attrib["Name"] != "":
                if document is not None:
                    if "ref" in document.attrib:
                        document = self.ref_check(document)
                    return error_msg
                else:
                    identifier = entity.attrib["id"]
                    referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                    if len(referenced) > 0:
                        for ref in referenced:
                            if ref.getparent().tag == "HasDocumentReferences":
                                return error_msg
            else:
                if document is None:
                    find = False
                    identifier = entity.attrib["id"]
                    referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                    if len(referenced) > 0:
                        for ref in referenced:
                            if ref.getparent().tag == "HasDocumentReferences":
                                find = True
                                break
                    if not find:
                        return error_msg
        elif ifcname == "IfcExternalReference":
            if not (
                ("Identification" in entity.attrib and entity.attrib["Identification"] != "")
                or ("Location" in entity.attrib and entity.attrib["Location"] != "")
                or ("Name" in entity.attrib and entity.attrib["Name"] != "")
            ):
                return "One of the attributes of IfcExternalReference should have a value assigned"
        elif ifcname == "IfcGridAxis":
            curve = entity.find("AxisCurve")
            if "ref" in curve.attrib:
                curve = self.ref_check(curve)
            ifccurve = curve.attrib[self.type] if self.type in curve.attrib else curve.tag
            dim = self.IfcDimensionSize(curve, ifccurve)
            if dim != 2:
                return "The dimensionality of the grid axis has to be 2"
        elif ifcname == "IfcDerivedUnit":
            elements = entity.find("Elements")
            if len(elements) == 1:
                if "ref" in elements[0].attrib:
                    elements[0] = self.ref_check(elements[0])
                if int(elements[0].attrib["Exponent"]) == 1:
                    return "Units as such shall not be re-defined as derived units"
        elif ifcname == "IfcNamedUnit":
            entity_type = entity.attrib[self.type] if self.type in entity.attrib else entity.tag
            unit = entity.attrib["UnitType"]
            if entity_type == "IfcSIUnit":
                dimensions = self.IfcDimensionsForSiUnit(entity.attrib["Name"])
            else:
                dimensions = entity.find("Dimensions")
                if "ref" in dimensions.attrib:
                    dimensions = self.ref_check(dimensions)
            result = self.IfcCorrectDimensions(unit, dimensions)
            if not result:
                return "Not the correct dimensions of the unit are established (tested through "\
                    "the function IfcCorrectDimensions)"
            elif result == "?":
                return "Not possible to check if the proper correct dimensions of the units are "\
                    "established through the function IfcCorrectDimensions"
        elif ifcname == "IfcArbitraryClosedProfileDef":
            curve = entity.find("OuterCurve")
            if "ref" in curve.attrib:
                curve = self.ref_check(curve)
            ifccurve = curve.attrib[self.type] if self.type in curve.attrib else curve.tag
            dim = self.IfcDimensionSize(curve, ifccurve)
            if dim != 2:
                return "The curve used for the outer curve definition shall have the "\
                    "dimensionality of 2"
        elif ifcname == "IfcAbitraryProfileDefWithVoids":
            if entity.attrib["ProfileType"].lower() != "area":
                return "The type of the profile shall be AREA, as it can only be involved in the "\
                    "definition of a swept area"
        elif ifcname == "IfcCircleHollowProfileDef":
            thickness = float(entity.attrib["WallThickness"])
            radius = float(entity.attrib["Radius"])
            if thickness >= radius:
                return "The wall thickness shall be smaller then the radius"
        elif ifcname == "IfcTable":
            rows = entity.find("Rows")
            if "ref" in rows.attrib:
                rows = self.ref_check(rows)
            if rows is not None:
                if "ref" in rows[0].attrib:
                    rows[0] = self.ref_check(rows[0])
                if "RowCells" not in rows[0].attrib or rows[0].attrib["RowCells"] == "":
                    base_number_of_cells = 0
                else:
                    base_number_of_cells = len(re.split(r"\s+", rows[0].attrib["RowCells"]))
                for row in rows:
                    if "ref" in row.attrib:
                        row = self.ref_check(row)
                    if "RowCells" not in row.attrib or row.attrib["RowCells"] == "":
                        number_of_cells = 0
                    else:
                        number_of_cells = len(re.split(r"\s+", row.attrib["RowCells"]))
                    if number_of_cells != base_number_of_cells:
                        return "Ensures that each row defines the same number of cells. The rule "\
                            "compares whether all other rows of the IfcTable have the same "\
                            "number of cells as the first row"


    def WR11(self, entity, ifcname, called_entity=None):
        """Checks different types of rules. More informations are found in the documentation.
        ----------
        This is used in IfcConstraint, IfcArbitraryOpenProfileDef & IfcShapeModel."""
        if ifcname == "IfcConstraint":
            grade = entity.attrib["ConstraintGrade"].lower()
            if grade == "userdefined":
                if (
                    "UserDefinedGrade" not in entity.attrib
                    or entity.attrib["UserDefinedGrade"] == ""
                ):
                    return "The attribute UserDefinedGrade must be asserted when the value of "\
                        "the IfcConstraintGradeEnum is set to USERDEFINED"
        elif ifcname == "IfcArbitraryOpenProfileDef":
            if entity.attrib["ProfileType"].lower() != "curve":
                return "The profile type is a .CURVE., an open profile can only be used to "\
                    "define a swept surface"
        elif ifcname == "IfcShapeModel":
            product_repr = entity.find("OfProductRepresentation")
            repr_map = entity.find("RepresentationMap")
            aspect = entity.find("OfShapeAspect")
            if not (product_repr is None and repr_map is None and aspect is None):
                if product_repr is None:
                    len_product_repr = 0
                else:
                    len_product_repr = 1 if len(product_repr) == 1 else 0
                if repr_map is None:
                    len_repr_map = 0
                else:
                    len_repr_map = 1 if len(repr_map) == 1 else 0
                if aspect is None:
                    len_aspect = 0
                else:
                    len_aspect = 1 if len(aspect) == 1 else 0
                if len_product_repr + len_repr_map + len_aspect != 1:
                    return "The IfcShapeModel shall be used by an IfcProductRepresentation, "\
                        "by an IfcRepresentationMap or by an IfcShapeAspect"
            else:
                identifier = entity.attrib["id"]
                referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                referenced.append(entity)
                ref1_val = 0
                ref2_val = 0
                ref3_val = 0
                for ref in referenced:
                    ref2 = ref.getparent()
                    ref2_type = ref2.attrib[self.type] if self.type in ref2.attrib else ref2.tag
                    if ref2_type != "ifcXML":
                        ref13 = ref.getparent().getparent()
                        ref13_type = (
                            ref13.attrib[self.type] if self.type in ref13.attrib else ref13.tag
                        )
                        if ref13_type != "ifcXML" and ref13_type.startswith("Ifc"):
                            if self.attr_check(ref13_type, "IfcProductRepresentation"):
                                ref1_val = 1
                            elif ref13_type == "IfcShapeAspect":
                                ref3_val = 1
                        if ref2_type.startswith("Ifc"):
                            if ref2_type == "IfcRepresentationMap":
                                ref2_val = 1
                    if ref1_val + ref2_val + ref3_val != 1:
                        return "The IfcShapeModel shall be used by an IfcProductRepresentation, "\
                            "by an IfcRepresentationMap or by an IfcShapeAspect"


    def WR12(self, entity, ifcname, called_entity=None):
        """Checks different types of rules. More informations are found in the documentation.
        ----------
        This is used in IfcArbitraryOpenProfileDef."""
        curve = entity.find("Curve")
        if "ref" in curve.attrib:
            curve = self.ref_check(curve)
        ifccurve = curve.attrib[self.type] if self.type in curve.attrib else curve.tag
        dimension = self.IfcDimensionSize(curve, ifccurve)
        if dimension != 2:
            return "The dimensionality of the curve shall be 2"


    def WR2(self, entity, ifcname, called_entity=None):
        """Checks different types of rules. More informations are found in the documentation.
        ----------
        This is used in IfcGridAxis, IfcDerivedUnit, IfcArbitraryClosedProfileDef,
        IfcAbitraryProfileDefWithVoids & IfcTable."""
        if ifcname == "IfcGridAxis":
            identifier = entity.attrib["id"]
            referenced_entities = self.tree.findall(f".//*[@ref='{identifier}']")
            print(identifier)
            print(len(referenced_entities))
            u = 1 if entity.find("PartOfU") is not None or entity.getparent().tag == "UAxes" else 0
            v = 1 if entity.find("PartOfV") is not None or entity.getparent().tag == "VAxes" else 0
            w = 1 if entity.find("PartOfW") is not None or entity.getparent().tag == "WAxes" else 0
            if u == 0:
                for ref in referenced_entities:
                    if ref.find("PartOfU") is not None or ref.getparent().tag == "UAxes":
                        u = 1
                        break
            if v == 0:
                for ref in referenced_entities:
                    if ref.find("PartOfV") is not None or ref.getparent().tag == "VAxes":
                        v = 1
                        break
            if w == 0:
                for ref in referenced_entities:
                    if ref.find("PartOfW") is not None or ref.getparent().tag == "WAxes":
                        w = 1
                        break
            print("----")
            print(u)
            print(v)
            print(w)
            if u + v + w != 1:
                return "The IfcGridAxis needs to be used by exactly one of the three attributes "\
                    "of IfcGrid: (1) UAxes; (2) VAxes; (3) WAxes, i.e. it can only refer to a "\
                    "single instance of IfcGrid in one of the three list of axes"
        elif ifcname == "IfcDerivedUnit":
            if entity.attrib["UnitType"].lower() == "userdefined":
                if "UserDefinedType" not in entity.attrib or entity.attrib["UserDefinedType"] == "":
                    return "When attribute UnitType has enumeration value USERDEFINED then "\
                        "attribute UserDefinedType shall also have a value"
        elif ifcname == "IfcArbitraryClosedProfileDef":
            curve = entity.find("OuterCurve")
            if "ref" in curve.attrib:
                curve = self.ref_check(curve)
            curve_type = curve.attrib[self.type] if self.type in curve.attrib else curve.tag
            if curve_type == "IfcLine":
                return "The outer curve shall not be of type IfcLine as IfcLine is not a "\
                    "closed curve"
        elif ifcname == "IfcAbitraryProfileDefWithVoids":
            curves = entity.find("InnerCurves")
            for curve in curves:
                if "ref" in curve.attrib:
                    curve = self.ref_check(curve)
                ifccurve = curve.tag
                dim = self.IfcDimensionSize(curve, ifccurve)
                if dim != 2:
                    return "All inner curves shall have the dimensionality of 2"
        elif ifcname == "IfcTable":
            rows = entity.find("Rows")
            if "ref" in rows.attrib:
                rows = self.ref_check(rows)
            heading = 0
            if rows is not None:
                for row in rows:
                    if "ref" in row.attrib:
                        row = self.ref_check(row)
                    if "IsHeading" in row.attrib and bool(BoolConv(row.attrib["IsHeading"])):
                        heading = heading + 1
                        if heading > 1:
                            return "The rule restricts the allowed number of heading rows to no "\
                                "more than one"


    def WR21(self, entity, ifcname, called_entity=None):
        """Checks different types of rules. More informations are found in the documentation.
        ----------
        This is used in IfcObjective, IfcLocalPlacement, IfcComplexProperty,
        IfcPropertyEnumeratedValue, IfcPropertyTableValue, IfcQuantityArea,
        IfcQuantityCount, IfcQuantityLength, IfcQuantityTime, IfcQuantityVolume,
        IfcQuantityWeight & IfcTopologyRepresentation."""
        if ifcname == "IfcObjective":
            if entity.attrib["ObjectiveQualifier"].lower() == "userdefined":
                if (
                    "UserDefinedQualifier" not in entity.attrib
                    or entity.attrib["UserDefinedQualifier"] == ""
                ):
                    return "The attribute UserDefinedQualifier must be asserted when the "\
                        "value of the ObjectiveQualifier is set to USERDEFINED"
        elif ifcname == "IfcLocalPlacement":
            placement_relto = (
                entity.getparent().getparent()
                if called_entity == "PlacementRelTo"
                else entity.find("PlacementRelTo")
            )
            relative_placement = entity.find("RelativePlacement")[0]
            if placement_relto is None:
                identifier = entity.attrib["id"]
                referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                if len(referenced) > 0:
                    for ref in referenced:
                        if ref.getparent().tag == "ReferencedByPlacements":
                            placement_relto = ref.getparent().getparent()
            if "ref" in relative_placement.attrib:
                relative_placement = self.ref_check(relative_placement)
            if placement_relto is not None:
                if "ref" in placement_relto.attrib:
                    placement_relto = self.ref_check(placement_relto)
                placement_relto_type = (
                    placement_relto.attrib[self.type]
                    if self.type in placement_relto.attrib
                    else placement_relto.tag
                )
                if self.attr_check(placement_relto_type, "IfcGridPlacement"):
                    return "It can't be properly checked if rule WR21 is applied"
                elif self.attr_check(placement_relto_type, "IfcLocalPlacement"):
                    if relative_placement.tag == "IfcAxis2Placement3D":
                        placement_relto = placement_relto.find("RelativePlacement")[0]
                        if "ref" in placement_relto.attrib:
                            placement_relto = self.ref_check(placement_relto)
                        if placement_relto.tag != "IfcAxis2Placement3D":
                            return "Ensures that a 3D local placement can only be relative "\
                                "(if exists) to a 3D parent local placement (and not to a 2D "\
                                "parent local placement)"
        elif ifcname == "IfcComplexProperty":
            current_id = entity.attrib["id"]
            properties = entity.find("HasProperties")
            if properties is None:
                properties = []
                identifier = entity.attrib["id"]
                referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                if len(referenced) > 0:
                    for ref in referenced:
                        if ref.getparent().tag == "PartOfComplex":
                            properties.append(ref.getparent().getparent())
                if called_entity == "HasProperties":
                    properties.append(entity.getparent().getparent())

            for prop in properties:
                if "ref" in prop.attrib:
                    prop = self.ref_check(prop)
                equal = self.elements_equal(entity, prop)
                if "id" in prop.attrib:
                    prop_id = prop.attrib["id"]
                else:
                    prop_id = prop.attrib["ref"]
                if equal or current_id == prop_id:
                    return "The IfcComplexProperty should not reference itself within the "\
                        "list of HasProperties"

        #According to the specification only the sizes are compared
        elif ifcname == "IfcPropertyEnumeratedValue":
            values = entity.find("EnumerationValues")
            reference = entity.find("EnumerationReference")
            if values is not None and reference is not None:
                if "ref" in values.attrib:
                    values = self.ref_check(values)
                if "ref" in reference.attrib:
                    reference = self.ref_check(reference)
                referenced_values = reference.find("EnumerationValues")
                referenced_list = []
                for child2 in referenced_values:
                    referenced_list.append(child2.text)
                for child1 in values:
                    if child1.text not in referenced_list:
                        return "Each value within the list of EnumerationValues shall be a "\
                            "member of the list of EnumerationValues at the referenced "\
                            "IfcPropertyEnumeration (provided that both, the EnumerationValues "\
                            "and EnumerationReference, are asserted)"
        elif ifcname == "IfcPropertyTableValue":
            defining_values = entity.find("DefiningValues")
            defined_values = entity.find("DefinedValues")
            if defining_values is not None and defined_values is not None:
                if len(defining_values) != len(defined_values):
                    return "Either both DefiningValues and DefinedValues are not provided, "\
                        "or the number of members in the list of DefiningValues shall be the "\
                        "same as the number of members in the list of DefinedValues"
            elif defining_values is None and defined_values is None:
                pass
            else:
                return "Either both DefiningValues and DefinedValues are not provided, "\
                    "or the number of members in the list of DefiningValues shall be the "\
                    "same as the number of members in the list of DefinedValues"
        elif ifcname == "IfcQuantityArea":
            unit = entity.find("Unit")
            if unit is not None:
                if "ref" in unit.attrib:
                    unit = self.ref_check(unit)
                if unit.attrib["UnitType"].lower() != "areaunit":
                    return "If a unit is given, the unit type shall be area unit"
        elif ifcname == "IfcQuantityCount":
            if float(entity.attrib["CountValue"]) < 0:
                return "The value of the count shall be greater than or equal to zero"
        elif ifcname == "IfcQuantityLength":
            unit = entity.find("Unit")
            if unit is not None:
                if "ref" in unit.attrib:
                    unit = self.ref_check(unit)
                if unit.attrib["UnitType"].lower() != "length":
                    return "If a unit is given, the unit type shall be a length unit"
        elif ifcname == "IfcQuantityTime":
            unit = entity.find("Unit")
            if unit is not None:
                if "ref" in unit.attrib:
                    unit = self.ref_check(unit)
                if unit.attrib["UnitType"].lower() != "timeunit":
                    return "If a unit is given, the unit type shall be time unit"
        elif ifcname == "IfcQuantityVolume":
            unit = entity.find("Unit")
            if unit is not None:
                if "ref" in unit.attrib:
                    unit = self.ref_check(unit)
                if unit.attrib["UnitType"].lower() != "volumeunit":
                    return "If a unit is given, the unit type shall be volume unit"
        elif ifcname == "IfcQuantityWeight":
            unit = entity.find("Unit")
            if unit is not None:
                if "ref" in unit.attrib:
                    unit = self.ref_check(unit)
                if unit.attrib["UnitType"].lower() != "massunit":
                    return "If a unit is given, the unit type shall be mass unit. NOTE: There is "\
                        "no distinction between the concept of 'Mass' and 'Weight' in the "\
                        "current IFC Release"
        elif ifcname == "IfcTopologyRepresentation":
            items = entity.find("Items")
            for item in items:
                if not self.attr_check(item.tag, "IfcTopologicalRepresentationItem"):
                    return "Only topological representation items should be used"


    def WR22(self, entity, ifcname, called_entity=None):
        """Checks different types of rules. More informations are found in the documentation.
        ----------
        This is used in IfcComplexProperty, IfcPropertyTableValue, IfcQuantityArea,
        IfcQuantityLength, IfcQuantityTime, IfcQuantityVolume, IfcQuantityWeight
        & IfcTopologyRepresentation."""
        if ifcname == "IfcComplexProperty":
            unique_list = []
            properties = entity.find("HasProperties")
            if properties is None:
                properties = []
                identifier = entity.attrib["id"]
                referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                if len(referenced) > 0:
                    for ref in referenced:
                        if ref.getparent().tag == "PartOfComplex":
                            properties.append(ref.getparent().getparent())
                if called_entity == "HasProperties":
                    properties.append(entity.getparent().getparent())

            for prop in properties:
                if "ref" in prop.attrib:
                    prop = self.ref_check(prop)
                if prop.attrib["Name"] in unique_list:
                    return "Each property within the complex property shall have a unique "\
                        "name attribute"
                else:
                    unique_list.append(prop.attrib["Name"])
        elif ifcname == "IfcPropertyTableValue":
            defining_values = entity.find("DefiningValues")
            if defining_values is not None:
                if "ref" in defining_values[0].attrib:
                    defining_values[0] = self.ref_check(defining_values[0])
                value_type = defining_values[0].tag
                for defval in defining_values:
                    if "ref" in defval.attrib:
                        defval = self.ref_check(defval)
                    if defval.tag != value_type:
                        return "If DefiningValues are provided, then all values within the "\
                            "list of DefiningValues shall have the same measure type"
        elif ifcname == "IfcQuantityArea":
            if float(entity.attrib["AreaValue"]) < 0:
                return "A valid area quantity shall be greater than or equal to zero"
        elif ifcname == "IfcQuantityLength":
            if float(entity.attrib["LengthValue"]) < 0:
                return "A valid length quantity shall be greater than or equal to zero"
        elif ifcname == "IfcQuantityTime":
            if float(entity.attrib["TimeValue"]) < 0:
                return "A valid weight quantity shall be greater than or equal to zero"
        elif ifcname == "IfcQuantityVolume":
            if float(entity.attrib["VolumeValue"]) < 0:
                return "A valid volume quantity shall be greater than or equal to zero"
        elif ifcname == "IfcQuantityWeight":
            if float(entity.attrib["WeightValue"]) < 0:
                return "A valid weight quantity shall be greater than or equal to zero"
        elif ifcname == "IfcTopologyRepresentation":
            if (
                "RepresentationType" not in entity.attrib
                or entity.attrib["RepresentationType"] == ""
            ):
                return "A representation type should be given to the topology representation"


    def WR23(self, entity, ifcname, called_entity=None):
        """Checks different types of rules. More informations are found in the documentation.
        ----------
        This is used in IfcPropertyTableValue & IfcTopologyRepresentation."""
        if ifcname == "IfcPropertyTableValue":
            defined_values = entity.find("DefinedValues")
            if defined_values is not None:
                if "ref" in defined_values[0].attrib:
                    defined_values[0] = self.ref_check(defined_values[0])
                value_type = defined_values[0].tag
                for defval in defined_values:
                    if defval.tag != value_type:
                        return "If DefinedValues are provided, then all values within the list "\
                            "of DefinedValues shall have the same measure type"
        elif ifcname == "IfcTopologyRepresentation":
            rep_type = entity.attrib["RepresentationType"]
            items = entity.find("Items")
            if "ref" in items.attrib:
                items = self.ref_check(items)
            result = self.IfcTopologyRepresentationTypes(rep_type, items)
            if not result:
                return "Checks the proper use of Items according to the RepresentationType"
            elif result == "?":
                return "Not possible to check the proper use of Items according to the "\
                    "RepresentationType, since the RespresentationType is unknown"


    def WR3(self, entity, ifcname, called_entity=None):
        """Checks different types of rules. More informations are found in the documentation.
        ----------
        This is used in IfcArbitraryClosedProfileDef & IfcAbitraryProfileDefWithVoids."""
        #What about IfcOffsetCurve3D? Not mentioned in specification.
        if ifcname == "IfcArbitraryClosedProfileDef":
            curve = entity.find("OuterCurve")
            if "ref" in curve.attrib:
                curve = self.ref_check(curve)
            curve_type = curve.attrib[self.type] if self.type in curve.attrib else curve.tag
            if curve_type == "IfcOffsetCurve2D":
                return "The outer curve shall not be of type IfcOffsetCurve2D as it should not "\
                    "be defined as an offset of another curve"
        elif ifcname == "IfcAbitraryProfileDefWithVoids":
            curves = entity.find("InnerCurves")
            for curve in curves:
                if curve.tag == "IfcLine":
                    return "None of the inner curves shall by of type IfcLine, as an IfcLine "\
                        "can not be a closed curve"


    def WR31(self, entity, ifcname, called_entity=None):
        """Checks different types of rules. More informations are found in the documentation.
        ----------
        This is used in IfcRelContainedInSpatialStructure, IfcTextLiteralWithExtent,
        IfcPropertyListValue, IfcOccupant, IfcDoorLiningProperties & IfcWindowLiningProperties."""
        if ifcname == "IfcRelContainedInSpatialStructure":
            elements = entity.find("RelatedElements")
            if elements is None:
                elements = []
                identifier = entity.attrib["id"]
                referenced = self.tree.findall(f".//*[@ref='{identifier}']")
                if len(referenced) > 0:
                    for ref in referenced:
                        if ref.tag == "ContainedInStructure" or ref.tag == "ContainedInStructures":
                            elements.append(ref.getparent())
                if called_entity == "RelatedElements":
                    elements.append(entity.getparent())

            for element in elements:
                if self.attr_check(element.tag, "IfcSpatialStructureElement"):
                    return "The relationship object shall not be used to include other spatial "\
                        "structure elements into a spatial structure element. The hierarchy of "\
                        "the spatial structure is defined using IfcRelAggregates"
        elif ifcname == "IfcTextLiteralWithExtent":
            extent = entity.find("Extent")
            if "ref" in extent.attrib:
                extent = self.ref_check(extent)
            extent_type = extent.attrib[self.type] if self.type in extent.attrib else extent.tag
            if extent_type == "IfcPlanarBox":
                return "The subtype of IfcPlanarExtent, IfcPlanarBox, should not be used to "\
                    "represent an Extent for the text literal"
        elif ifcname == "IfcPropertyListValue":
            values = entity.find("ListValues")
            value_type = values[0].tag
            for val in values:
                if val.tag != value_type:
                    return "All values within the list of values shall be of the same measure type"
        elif ifcname == "IfcOccupant":
            if (
                "PredefinedType" in entity.attrib
                and entity.attrib["PredefinedType"].lower() == "userdefined"
            ):
                if "ObjectType" not in entity.attrib or entity.attrib["ObjectType"] == "":
                    return "The attribute ObjectType must be asserted when the value of the "\
                        "IfcOccupantTypeEnum is set to USERDEFINED"
        elif ifcname == "IfcDoorLiningProperties":
            if "LiningDepth" in entity.attrib and entity.attrib["LiningDepth"] != "":
                if "LiningThickness" not in entity.attrib or entity.attrib["LiningThickness"] == "":
                    return "Either both parameter, LiningDepth and LiningThickness are given, "\
                        "or only the LiningThickness, then the LiningDepth is variable. It is "\
                        "not valid to only assert the LiningDepth"
        elif ifcname == "IfcWindowLiningProperties":
            if "LiningDepth" in entity.attrib and entity.attrib["LiningDepth"] != "":
                if "LiningThickness" not in entity.attrib or entity.attrib["LiningThickness"] == "":
                    return "Either both parameter, LiningDepth and LiningThickness are given, "\
                        "or only the LiningThickness, then the LiningDepth is variable. It is "\
                        "not valid to only assert the LiningDepth"


    def WR32(self, entity, ifcname, called_entity=None):
        """Checks different types of rules. More informations are found in the documentation.
        ----------
        This is used in IfcDoorLiningProperties & IfcWindowLiningProperties."""
        if ifcname == "IfcDoorLiningProperties":
            if "ThresholdDepth" in entity.attrib and entity.attrib["ThresholdDepth"] != "":
                if (
                    "ThresholdThickness" not in entity.attrib
                    or entity.attrib["ThresholdThickness"] == ""
                ):
                    return "Either both parameter, ThresholdDepth and ThresholdThickness are "\
                        "given, or only the ThresholdThickness, then the ThresholdDepth is "\
                        "variable. It is not valid to only assert the ThresholdDepth"
        elif ifcname == "IfcWindowLiningProperties":
            if (
                "SecondTransomOffset" in entity.attrib
                and entity.attrib["SecondTransomOffset"] != ""
            ):
                if (
                    "FirstTransomOffset" not in entity.attrib
                    or entity.attrib["FirstTransomOffset"] == ""
                ):
                    return "Either both parameter, FirstTransomOffset and SecondTransomOffset "\
                        "are given, or only the FirstTransomOffset, or none of both. It is not "\
                        "valid to only assert the SecondTransomOffset"


    def WR33(self, entity, ifcname, called_entity=None):
        """Checks different types of rules. More informations are found in the documentation.
        ----------
        This is used in IfcDoorLiningProperties & IfcWindowLiningProperties."""
        if ifcname == "IfcDoorLiningProperties":
            if "TransomOffset" in entity.attrib and entity.attrib["TransomOffset"] != "":
                if (
                    "TransomThickness" not in entity.attrib
                    or entity.attrib["TransomThickness"] == ""
                ):
                    return "Either both parameter, TransomDepth and TransomThickness are given, "\
                        "or none of them"
            else:
                if "TransomThickness" in entity.attrib and entity.attrib["TransomThickness"] != "":
                    return "Either both parameter, TransomDepth and TransomThickness are given, "\
                        "or none of them"
        elif ifcname == "IfcWindowLiningProperties":
            if (
                "SecondMullionOffset" in entity.attrib
                and entity.attrib["SecondMullionOffset"] != ""
            ):
                if (
                    "FirstMullionOffset" not in entity.attrib
                    or entity.attrib["FirstMullionOffset"] == ""
                ):
                    return "Either both parameter, FirstMullionOffset and SecondMullionOffset "\
                        "are given, or only the FirstMullionOffset, or none of both. It is not "\
                        "valid to only assert the SecondMullionOffset"


    def WR34(self, entity, ifcname, called_entity=None):
        """Checks different types of rules. More informations are found in the documentation.
        ----------
        This is used in IfcDoorLiningProperties & IfcWindowLiningProperties."""
        if ifcname == "IfcDoorLiningProperties":
            if "CasingDepth" in entity.attrib and entity.attrib["CasingDepth"] != "":
                if "CasingThickness" not in entity.attrib or entity.attrib["CasingThickness"] == "":
                    return "Either both parameter, the CasingDepth and the CasingThickness, "\
                        "are given, or none of them"
            else:
                if "CasingThickness" in entity.attrib and entity.attrib["CasingThickness"] != "":
                    return "Either both parameter, the CasingDepth and the CasingThickness, "\
                        "are given, or none of them"
        elif ifcname == "IfcWindowLiningProperties":
            defines = entity.find("DefinesType")
            if defines is None:
                return "The IfcWindowLiningProperties shall only be used in the context of an "\
                    "IfcWindowType (or IfcWindowStyle)"
            else:
                for define in defines:
                    if define.tag != "IfcWindowType" and define.tag != "IfcWindowStyle":
                        return "The IfcWindowLiningProperties shall only be used in the context "\
                            "of an IfcWindowType (or IfcWindowStyle)"


    def WR35(self, entity, ifcname, called_entity=None):
        """Checks different types of rules. More informations are found in the documentation.
        ----------
        This is used in IfcDoorLiningProperties."""
        #Following rule restriction defined via express specification
        defines = entity.find("DefinesType")
        if defines is None:
            return "The IfcDoorLiningProperties shall only be used in the context of an "\
                "IfcDoorType (or IfcDoorStyle)"
        else:
            for define in defines:
                if define.tag != "IfcDoorType" and define.tag != "IfcDoorStyle":
                    return "The IfcDoorLiningProperties shall only be used in the context "\
                        "of an IfcDoorType (or IfcDoorStyle)"


    def WR41(self, entity, ifcname, called_entity=None):
        """Checks different types of rules. More informations are found in the documentation.
        ----------
        This is used in IfcSpatialStructureElement."""
        decompose = entity.find("Decomposes")
        if decompose is None:
            decomposed_by = entity.getparent().getparent().getparent()
            if decomposed_by.tag != "IsDecomposedBy":
                return "All spatial structure elements shall be associated (using the "\
                    "IfcRelAggregates relationship) with another spatial structure element, "\
                    "or with IfcProject"
            else:
                rel_obj = decomposed_by.getparent()
                rel_obj_type = (
                    rel_obj.attrib[self.type] if self.type in rel_obj.attrib else rel_obj.tag
                )
                allowed_obj = ["IfcProject", "IfcSpatialStructureElement"]
                if not self.attr_list_check(rel_obj_type, allowed_obj):
                    return "All spatial structure elements shall be associated (using the "\
                        "IfcRelAggregates relationship) with another spatial structure element, "\
                        "or with IfcProject"

        else:
            if "ref" in decompose[0].attrib:
                decompose[0] = self.ref_check(decompose[0])
            rel_obj = decompose[0].find("RelatingObject")
            if "ref" in rel_obj.attrib:
                rel_obj = self.ref_check(rel_obj)
            rel_obj = rel_obj.attrib[self.type] if self.type in rel_obj.attrib else rel_obj.tag
            allowed_obj = ["IfcProject", "IfcSpatialStructureElement"]
            if not self.attr_list_check(rel_obj, allowed_obj):
                return "All spatial structure elements shall be associated (using the "\
                    "IfcRelAggregates relationship) with another spatial structure element, "\
                    "or with IfcProject"


    def WeightValuesGreaterZero(self, entity, ifcname, called_entity=None):
        """Checks if all weights are greater than 0.
        ----------
        This is used in IfcRationalBSplineSurfaceWithKnots."""
        weights = re.split(r"\s+", str(entity.attrib["WeightsData"]))
        for val in weights:
            if float(val) <= 0.0:
                return "The weight value associated with each control point shall be greater "\
                    "than zero"


    def WeightsGreaterZero(self, entity, ifcname, called_entity=None):
        """Checks if all weights are greater than 0.
        ----------
        This is used in IfcRationalBSplineCurveWithKnots."""
        weights = re.split(r"\s+", str(entity.attrib["WeightsData"]))
        for val in weights:
            if float(val) <= 0.0:
                return "All the weights shall have values greater than 0.0"
