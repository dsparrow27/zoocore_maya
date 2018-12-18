from maya import cmds
from maya.api import OpenMaya as om2

from zoo.libs.maya.api import nodes
from zoo.libs.maya.api import plugs


def distanceBetween(firstNode, secondNode, name):
    """Creates a distance between node and connects the 'firstNode' and 'secondNode' world space
    matrices.

    :param firstNode: The start transform node
    :type firstNode: MObject
    :param secondNode: The second transform node
    :type secondNode: MObject
    :return:  the Three nodes created by the function in the form of a tuple, the first element \
    is the distance between node, the second is the start node decompose matrix, the third element \
    is the second node decompose matrix.
    :rtype: tuple(om2.MObject, om2.MObject, om2.MObject)  
    """
    firstFn = om2.MFnDependencyNode(firstNode)
    secondFn = om2.MFnDependencyNode(secondNode)

    distanceBetweenNode = nodes.createDGNode(name, "distanceBetween")
    distFn = om2.MFnDependencyNode(distanceBetweenNode)
    firstFnWorldMat = firstFn.findPlug("worldMatrix", False)
    firstFnWorldMat.evaluateNumElements()
    secondFnWorldMat = secondFn.findPlug("worldMatrix", False)
    secondFnWorldMat.evaluateNumElements()

    plugs.connectPlugs(firstFnWorldMat.elementByPhysicalIndex(0), distFn.findPlug("inMatrix1", False))
    plugs.connectPlugs(secondFnWorldMat.elementByPhysicalIndex(0), distFn.findPlug("inMatrix2", False))

    return distanceBetweenNode


def multiplyDivide(input1, input2, operation, name):
    """
    List of operations::

        no operation = 0,
        multipy = 1,
        divide = 2,
        power = 3

    :param input1:the node attribute to connect to the input1 value or use int for value
    :type input1: MPlug or MVector
    :param input2:the node attribute to connect to the input2 value or use int for value
    :type input2: MPlug or MVector
    :param operation: the int value for operation
    :type operation: int
    :return, the multiplyDivide node MObject
    :rtype: MObject
    """

    mult = om2.MFnDependencyNode(nodes.createDGNode(name, "multiplyDivide"))
    # assume connection type
    if isinstance(input1, om2.MPlug):
        plugs.connectPlugs(input1, mult.findPlug("input1", False))
    # plug set
    else:
        plugs.setPlugValue(mult.findPlug("input1", False), input1)
    if isinstance(input2, om2.MPlug):
        plugs.connectPlugs(input2, mult.findPlug("input2", False))
    else:
        plugs.setPlugValue(mult.findPlug("input2", False), input1)
    plugs.setPlugValue(mult.findPlug("operation", False), operation)

    return mult.object()


def blendColors(color1, color2, name, blender):
    blendFn = om2.MFnDependencyNode(nodes.createDGNode(name, "blendColors"))
    if isinstance(color1, om2.MPlug):
        plugs.connectPlugs(color1, blendFn.findPlug("color1", False))
    else:
        plugs.setPlugValue(blendFn.findPlug("color1", False), color1)
    if isinstance(color2, om2.MPlug):
        plugs.connectPlugs(color2, blendFn.findPlug("color2", False))
    else:
        plugs.setPlugValue(blendFn.findPlug("color2", False), color2)
    if isinstance(blender, om2.MPlug):
        plugs.connectPlugs(blender, blendFn.findPlug("blender", False))
    else:
        plugs.setPlugValue(blendFn.findPlug("blender", False), blender)
    return blendFn.object()


def floatMath(floatA, floatB, operation, name):
    floatMathFn = om2.MFnDependencyNode(nodes.createDGNode(name, "floatMath"))
    if isinstance(floatA, om2.MPlug):
        plugs.connectPlugs(floatA, floatMathFn.findPlug("floatA", False))
    else:
        plugs.setPlugValue(floatMathFn.findPlug("floatA", False), floatA)

    if isinstance(floatB, om2.MPlug):
        plugs.connectPlugs(floatB, floatMathFn.findPlug("floatB", False))
    else:
        plugs.setPlugValue(floatMathFn.findPlug("floatB", False), floatB)
    plugs.setPlugValue(floatMathFn.findPlug("operation", False), operation)
    return floatMathFn.object()


def blendTwoAttr(input1, input2, blender, name):
    fn = om2.MFnDependencyNode(nodes.createDGNode(name, "blendTwoAttr"))
    inputArray = fn.findPlug("input", False)
    plugs.connectPlugs(input1, inputArray.elementByLogicalIndex(-1))
    plugs.connectPlugs(input2, inputArray.elementByLogicalIndex(-1))
    plugs.connectPlugs(blender, fn.findPlug("attributesBlender", False))
    return fn.object()


def pairBlend(name, inRotateA=None, inRotateB=None, inTranslateA=None, inTranslateB=None, weight=None,
              rotInterpolation=None):
    blendPairNode = om2.MFnDependencyNode(nodes.createDGNode(name, "pairBlend"))
    if inRotateA is not None:
        plugs.connectPlugs(inRotateA, blendPairNode.findPlug("inRotate1", False))
    if inRotateB is not None:
        plugs.connectPlugs(inRotateB, blendPairNode.findPlug("inRotate2", False))
    if inTranslateA is not None:
        plugs.connectPlugs(inTranslateA, blendPairNode.findPlug("inTranslate1", False))
    if inTranslateB is not None:
        plugs.connectPlugs(inTranslateB, blendPairNode.findPlug("inTranslate2", False))
    if weight is not None:
        if isinstance(weight, om2.MPlug):
            plugs.connectPlugs(weight, blendPairNode.findPlug("weight", False))
        else:
            plugs.setPlugValue(blendPairNode.findPlug("weight", False), weight)
    if rotInterpolation is not None:
        if isinstance(rotInterpolation, om2.MPlug):
            plugs.connectPlugs(rotInterpolation, blendPairNode.findPlug("rotInterpolation", False))
        else:
            plugs.setPlugValue(blendPairNode.findPlug("rotInterpolation", False), rotInterpolation)
    return blendPairNode.object()


def conditionVector(firstTerm, secondTerm, colorIfTrue, colorIfFalse, operation, name):
    """
    :param firstTerm: 
    :type firstTerm: om2.MPlug or float
    :param secondTerm: 
    :type secondTerm: om2.MPlug or float 
    :param colorIfTrue: seq of MPlugs or a single MPlug(compound) 
    :type colorIfTrue: om2.MPlug or list(om2.Plug) or om2.MVector
    :param colorIfFalse: seq of MPlugs or a single MPlug(compound)
    :type colorIfFalse: om2.MPlug or list(om2.Plug) or om2.MVector 
    :param operation: the comparsion operator
    :type operation: int
    :param name: the new name for the node
    :type name: str
    :return: 
    :rtype: om2.MObject
    """
    condNode = om2.MFnDependencyNode(nodes.createDGNode(name, "condition"))
    if isinstance(operation, int):
        plugs.setPlugValue(condNode.findPlug("operation", False), operation)
    else:
        plugs.connectPlugs(operation, condNode.findPlug("operation", False))

    if isinstance(firstTerm, float):
        plugs.setPlugValue(condNode.findPlug("firstTerm", False), firstTerm)
    else:
        plugs.connectPlugs(firstTerm, condNode.findPlug("firstTerm", False))

    if isinstance(secondTerm, float):
        plugs.setPlugValue(condNode.findPlug("secondTerm", False), secondTerm)
    else:
        plugs.connectPlugs(secondTerm, condNode.findPlug("secondTerm", False))
    if isinstance(colorIfTrue, om2.MPlug):
        plugs.connectPlugs(colorIfTrue, condNode.findPlug("colorIfTrue", False))
    elif isinstance(colorIfTrue, om2.MVector):
        plugs.setPlugValue(condNode.findPlug("colorIfTrue", False), colorIfTrue)
    else:
        color = condNode.findPlug("colorIfTrue", False)
        # expecting seq of plugs
        for i, p in enumerate(colorIfTrue):
            if p is None:
                continue
            child = color.child(i)
            if isinstance(p, om2.MPlug):
                plugs.connectPlugs(p, child)
                continue
            plugs.setPlugValue(child, p)
    if isinstance(colorIfFalse, om2.MPlug):
        plugs.connectPlugs(colorIfFalse, condNode.findPlug("colorIfFalse", False))
    elif isinstance(colorIfFalse, om2.MVector):
        plugs.setPlugValue(condNode.findPlug("colorIfFalse", False), colorIfFalse)
    else:
        color = condNode.findPlug("colorIfFalse", False)
        # expecting seq of plugs
        for i, p in enumerate(colorIfFalse):
            if p is None:
                continue
            child = color.child(i)
            if isinstance(p, om2.MPlug):
                plugs.connectPlugs(p, child)
                continue
            plugs.setPlugValue(child, p)
    return condNode.object()


def createAnnotation(rootObj, endObj, text=None, name=None):
    name = name or "annotation"
    rootDag = om2.MFnDagNode(rootObj)
    boundingBox = rootDag.boundingBox
    center = om2.MVector(boundingBox.center)
    transform = nodes.createDagNode("_".join([name, "loc"]), "transform", parent=rootObj)
    nodes.setTranslation(transform, nodes.getTranslation(rootObj, om2.MSpace.kWorld), om2.MSpace.kWorld)
    annotationNode = nodes.asMObject(cmds.annotate(nodes.nameFromMObject(transform), tx=text))
    annParent = nodes.getParent(annotationNode)
    nodes.rename(annParent, name)
    plugs.setPlugValue(om2.MFnDagNode(annotationNode).findPlug("position", False), center)
    nodes.setParent(annParent, endObj, False)
    return annotationNode, transform


def createMultMatrix(name, inputs, output):
    multMatrix = nodes.createDGNode(name, "multMatrix")
    fn = om2.MFnDependencyNode(multMatrix)
    compound = fn.findPlug("matrixIn", False)
    compound.evaluateNumElements()

    for i in xrange(1, len(inputs)):
        inp = inputs[i]
        if isinstance(inp, om2.MPlug):
            plugs.connectPlugs(inp, compound.elementByLogicalIndex(i))
            continue
        plugs.setPlugValue(compound.elementByLogicalIndex(i), inp)
    inp = inputs[0]
    if isinstance(inp, om2.MPlug):
        plugs.connectPlugs(inp, compound.elementByLogicalIndex(0))
    else:
        plugs.setPlugValue(compound.elementByLogicalIndex(0), inp)
    if output is not None:
        plugs.connectPlugs(fn.findPlug("matrixSum", False), output)

    return multMatrix


def createDecompose(name, destination, translateValues, scaleValues, rotationValues, inputMatrixPlug=None):
    """Creates a decompose node and connects it to the destination node.

    :param inputMatrixPlug: The input matrix plug to connect from.
    :type inputMatrixPlug: om2.MPlug
    :param translateValues: the x,y,z to apply must have all three if all three are true then the compound will be \
    connected.
    :type translateValues: list(str)
    :param scaleValues: the x,y,z to apply must have all three if all three are true then the compound will be \
    connected.
    :type scaleValues: list(str)
    :param rotationValues: the x,y,z to apply must have all three if all three are true then the compound will be \
    connected.
    :type rotationValues: list(str)
    :param destination: the node to connect to
    :type destination: om2.MObject
    :return: the decompose node
    :rtype: om2.MObject
    """
    decompose = nodes.createDGNode(name, "decomposeMatrix")
    mfn = om2.MFnDependencyNode(decompose)

    if inputMatrixPlug is not None:
        plugs.connectPlugs(inputMatrixPlug, mfn.findPlug("inputMatrix", False))
    if destination:
        destFn = om2.MFnDependencyNode(destination)
        # translation
        plugs.connectVectorPlugs(mfn.findPlug("outputTranslate", False), destFn.findPlug("translate", False),
                                 translateValues)
        plugs.connectVectorPlugs(mfn.findPlug("outputRotate", False), destFn.findPlug("rotate", False), rotationValues)
        plugs.connectVectorPlugs(mfn.findPlug("outputScale", False), destFn.findPlug("scale", False), scaleValues)
    return decompose


def createReverse(name, inputs, outputs):
    """

    :param name: The name for the reverse node to have, must be unique
    :type name: str
    :param inputs: If Plug then the plug must be a compound.
    :type inputs: om2.MPlug or tuple
    :param outputs: If Plug then the plug must be a compound.
    :type outputs: om2.MPlug or tuple
    :return: OpenMaya 2.0 MObject representing the reverse node
    :rtype: om2.MObject
    :raises: ValueError if the inputs or outputs is not an om2.MPlug
    """
    rev = nodes.createDGNode(name, "reverse")
    fn = om2.MFnDependencyNode(rev)
    inPlug = fn.findPlug("input", False)
    ouPlug = fn.findPlug("output", False)

    if isinstance(inputs, om2.MPlug):
        if inputs.isCompound:
            plugs.connectPlugs(inputs, inPlug)
            return rev
        else:
            raise ValueError("Inputs Argument must be a compound when passing a single plug")
    elif isinstance(outputs, om2.MPlug):
        if outputs.isCompound:
            plugs.connectPlugs(outputs, ouPlug)
            return rev
        else:
            raise ValueError("Outputs Argument must be a compound when passing a single plug")
    # passed the dealings with om2.MPlug so deal with seq type
    for childIndex in range(len(inputs)):
        inA = inputs[childIndex]
        if inA is None:
            continue
        plugs.connectPlugs(inputs[childIndex], inPlug.child(childIndex))

    for childIndex in range(len(outputs)):
        inA = outputs[childIndex]
        if inA is None:
            continue
        plugs.connectPlugs(ouPlug.child(childIndex), outputs[childIndex])

    return rev


def createSetRange(name, value, min_, max_, oldMin, oldMax, outValue=None):
    """ Generates and connects a setRange node, input/output arguments take an iterable, possibles values are om2.MPlug,
    float or None , if a value is None it will be skipped this is useful when two or of three you want connected or set
    to a value but the other is left to the default state. If MPlug is passed and its a compound it'll be connected.

    :param name: the new name for the set Range node
    :type name: str
    :param value:
    :type value: iterable(om2.MPlug or float or None)
    :param min_:
    :type min_: iterable(om2.MPlug or float or None)
    :param max_:
    :type max_: iterable(om2.MPlug or float or None)
    :param oldMin:
    :type oldMin: iterable(om2.MPlug or float or None)
    :param oldMax:
    :type oldMax: iterable(om2.MPlug or float or None)
    :param outValue:
    :type outValue: iterable(om2.MPlug or float or None)
    :return: the created setRange node
    :rtype: om2.MObject

    .. code-block:: python

        one = nodes.createDagNode("one", "transform")
        two = nodes.createDagNode("two", "transform")
        end = nodes.createDagNode("end", "transform")

        oneFn = om2.MFnDagNode(one)
        twoFn = om2.MFnDagNode(two)
        endFn = om2.MFnDagNode(end)
        values = [oneFn.findPlug("translate", False)]
        min_ = [twoFn.findPlug("translate", False)]
        max_ = [twoFn.findPlug("translate", False)]
        oldMax = [0.0,180,360]
        oldMin = [-10,-720,-360]
        reload(creation)
        outValues = [endFn.findPlug("translateX", False), endFn.findPlug("translateY", False), None]
        pma = creation.createSetRange("test_pma", values, min_, max_, oldMin, oldMax, outValues)

    """
    setRange = nodes.createDGNode(name, "setRange")
    fn = om2.MFnDependencyNode(setRange)
    valuePlug = fn.findPlug("value", False)
    oldMinPlug = fn.findPlug("oldMin", False)
    oldMaxPlug = fn.findPlug("oldMax", False)
    minPlug = fn.findPlug("min", False)
    maxPlug = fn.findPlug("max", False)

    # deal with all the inputs
    # source list, destination plug
    for source, destination in ((value, valuePlug), (min_, minPlug), (max_, maxPlug), (oldMin, oldMinPlug),
                                (oldMax, oldMaxPlug)):
        if source is None:
            continue
        for index, inner in enumerate(source):
            if inner is None:
                continue
            if isinstance(inner, om2.MPlug):
                if inner.isCompound:
                    plugs.connectPlugs(inner, destination)
                    break
                child = destination.child(index)
                plugs.connectPlugs(inner, child)
                continue
            child = destination.child(index)
            plugs.setPlugValue(child, inner)
    if outValue is None:
        return setRange
    outPlug = fn.findPlug("outValue", False)
    # now the outputs
    for index, out in enumerate(outValue):
        if out is None:
            continue
        if isinstance(out, om2.MPlug):
            if out.isCompound:
                plugs.connectPlugs(outPlug, out)
                break
            child = outPlug.child(index)
            plugs.connectPlugs(child, out)
            continue
        child = outPlug.child(index)
        # not a plug must be a plug value
        plugs.setPlugValue(child, out)
    return setRange


def createPlusMinusAverage1D(name, inputs, output=None, operation=1):
    """
    :param name: the plus minus average node name
    :type name: str
    :param inputs:
    :type inputs: iterable(plug or float)
    :param output:
    :type output: iterable(plug)
    :return: The plus minus average MObject
    :rtype: om2.MObject

    .. code-block:: python

        one = nodes.createDagNode("one", "transform")
        two = nodes.createDagNode("two", "transform")
        end = nodes.createDagNode("end", "transform")

        oneFn = om2.MFnDagNode(one)
        twoFn = om2.MFnDagNode(two)
        endFn = om2.MFnDagNode(end)
        inputs = [oneFn.findPlug("translateX", False), twoFn.findPlug("translateX", False)]
        outputs = [endFn.findPlug("translateX", False)]
        pma = creation.createPlusMinusAverage1D("test_pma", inputs, outputs)
        # Result: <OpenMaya.MObject object at 0x000002AECB23AE50> #

    """
    pma = nodes.createDGNode(name, "plusMinusAverage")
    fn = om2.MFnDependencyNode(pma)
    inPlug = fn.findPlug("input1D", False)
    fn.findPlug("operation", False).setInt(operation)
    for i, p in enumerate(inputs):
        if p is None:
            continue
        child = plugs.nextAvailableElementPlug(inPlug)
        if isinstance(p, om2.MPlug):
            plugs.connectPlugs(p, child)
            continue

        plugs.setPlugValue(child, p)

    if output is not None:
        ouPlug = fn.findPlug("output1D", False)
        for out in output:
            plugs.connectPlugs(ouPlug, out)
    return pma


def createPlusMinusAverage2D(name, inputs, output=None, operation=1):
    """
    :param name: the plus minus average node name
    :type name: str
    :param inputs:
    :type inputs: iterable(plug or float)
    :param output:
    :type output: iterable(plug)
    :return: The plus minus average MObject
    :rtype: om2.MObject
    """
    pma = nodes.createDGNode(name, "plusMinusAverage")
    fn = om2.MFnDependencyNode(pma)
    inPlug = fn.findPlug("input2D", False)
    fn.findPlug("operation", False).setInt(operation)
    for i, p in enumerate(inputs):
        if p is None:
            continue
        child = plugs.nextAvailableElementPlug(inPlug)
        if isinstance(p, om2.MPlug):
            plugs.connectPlugs(p, child)
            continue
        plugs.setPlugValue(child, p)

    if output is not None:
        ouPlug = fn.findPlug("output2D", False)
        for index, out in enumerate(output):
            if out is None:
                continue
            plugs.connectPlugs(ouPlug, out)
    return pma


def createPlusMinusAverage3D(name, inputs, output=None, operation=1):
    """
    :param name: the plus minus average node name
    :type name: str
    :param inputs:
    :type inputs: iterable(plug or float)
    :param output:
    :type output: iterable(plug)
    :return: The plus minus average MObject
    :rtype: om2.MObject

    .. code-block:: python

        one = nodes.createDagNode("one", "transform")
        two = nodes.createDagNode("two", "transform")
        end = nodes.createDagNode("end", "transform")

        oneFn = om2.MFnDagNode(one)
        twoFn = om2.MFnDagNode(two)
        endFn = om2.MFnDagNode(end)
        inputs = [oneFn.findPlug("translate", False), twoFn.findPlug("translate", False)]
        outputs = [endFn.findPlug("translate", False)]
        pma = creation.createPlusMinusAverage3D("test_pma", inputs, outputs)
        # Result: <OpenMaya.MObject object at 0x000002AECB23AE50> #
        
    """
    pma = nodes.createDGNode(name, "plusMinusAverage")
    fn = om2.MFnDependencyNode(pma)
    inPlug = fn.findPlug("input3D", False)
    fn.findPlug("operation", False).setInt(operation)
    for i, p in enumerate(inputs):
        if p is None:
            continue
        child = plugs.nextAvailableElementPlug(inPlug)
        if isinstance(p, om2.MPlug):
            plugs.connectPlugs(p, child)
            continue
        plugs.setPlugValue(child, p)

    if output is not None:
        ouPlug = fn.findPlug("output3D", False)
        for index, out in enumerate(output):
            if out is None:
                continue
            plugs.connectPlugs(ouPlug, out)
    return pma


def createController(node, name, parent=None, visibilitySwitch=None):
    """Create's a maya kControllerTag node and attaches it to the node

    ..code-block: python

        from zoo.libs.maya.api import scene, nodes
        from maya.api import OpenMaya as om2
        sel = scene.getSelectedNodes()
        ctrlNode = creation.createController(sel[0], "test_tag")
        # Result: MObject

    :param node: The node to add as the controller
    :type node: om2.MObject
    :param name:
    :type name: str
    :param parent: The parent kController node
    :type parent: om2.MObject
    :param visibilitySwitch: The MPlug which will control to visibility mode. defaults to None
    :type visibilitySwitch: om2.MPlug
    :return: The controlTag Mobject
    :rtype: om2.MObject
    """
    controller = nodes.createDGNode(name, "controller")
    fn = om2.MFnDependencyNode(controller)
    ctrlFn = om2.MFnDependencyNode(node)
    # connect up the controllerObject
    plugs.connectPlugs(ctrlFn.findPlug("message", False), fn.findPlug("controllerObject", False))
    if parent is not None and parent.apiType() == om2.MFn.kControllerTag:
        parentFn = om2.MFnDependencyNode(parent)
        plugs.connectPlugs(parentFn.findPlug("prepopulate", False),
                           fn.findPlug("prepopulate", False))
        plugs.connectPlugs(fn.findPlug("parent", False),
                           plugs.nextAvailableDestElementPlug(parentFn.findPlug("children", False)))
    # handle the visibility mode MPlug if provided
    if visibilitySwitch is not None:
        plugs.connectPlugs(visibilitySwitch, fn.findPlug("visibilityMode", False))
    return controller
