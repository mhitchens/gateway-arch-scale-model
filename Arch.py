"""
An Autodesk Fusion script to generate the 3D geometry of the St. Louis Gateway Arch

IMPORTANT: You must turn off design history before running this script

This works best when the units for your model are set to feet. The geometry is actual size, about 630ft high.

Matthew Hitchens <matt@hitchens.net>
MIT Licensed
"""

import traceback
import adsk.core
import adsk.fusion
import math

def profileForLine(line: adsk.fusion.SketchLine, sketch: adsk.fusion.Sketch) -> adsk.fusion.Profile:
    for i in range(sketch.profiles.count):
        profile = sketch.profiles.item(i)
        for j in range(profile.profileLoops.count):
            profileLoop = profile.profileLoops.item(j)
            for k in range(profileLoop.profileCurves.count):
                profileCurve = profileLoop.profileCurves.item(k)
                if profileCurve.sketchEntity.entityToken == line.entityToken:
                    return profile

def pointForFtCoords(x: float, y: float, z: float, unitsManager: adsk.core.UnitsManager) -> adsk.core.Point3D:
    unitFormat = '{:.4f} ft'
    return adsk.core.Point3D.create(unitsManager.evaluateExpression(unitFormat.format(x), unitFormat.format(y), unitFormat.format(z)))

# Initialize the global variables for the Application and UserInterface objects.
app = adsk.core.Application.get()
ui  = app.userInterface

def run(_context: str):
    try:
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        unitsManager = design.unitsManager
        rootComponent = design.rootComponent

        # we'll do all our work on a new component called 'Gateway Arch', if it already exists we'll delete it
        archName = 'Gateway Arch'
        for o in rootComponent.occurrences.asArray():
            if o.component.name == archName:
                o.deleteMe()
        archOcc = rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        archComp = archOcc.component
        archComp.name = archName
        sketches = archComp.sketches

        # TODO: I still need to understand how these values from the blueprint were derived
        xCoords = [
            7.736, 15.4528, 23.1312, 30.7496, 38.2872, 45.7256, 53.0456, 60.228, 67.2624, 74.1376, 
            80.8448, 87.3768, 93.7677, 100.0101, 106.098, 112.1331, 118.103, 123.9978, 129.8074, 135.5237, 
            141.1407, 146.6567, 152.0684, 157.3727, 162.5677, 167.6533, 172.6304, 177.5, 182.263, 186.9213, 
            191.4791, 195.945, 200.2592, 204.4297, 208.4644, 212.3717, 216.159, 219.8329, 223.3986, 226.8496, 
            230.1923, 233.4326, 236.5765, 239.6292, 242.5954, 245.4796, 248.2861, 251.0188, 253.6814, 256.2773, 
            258.8096, 261.2812, 263.6952, 266.0538, 268.3595, 270.6143, 272.8207, 274.9804, 277.0955, 279.1677, 
            281.1988, 283.1902, 285.1434, 287.0597, 288.9406, 290.7872, 292.6007, 294.3824, 296.1334, 297.8546, 
            299.5458
        ]

        afc = 625.0925
        aQb = math.pow(54.0, 2)
        aQt = math.pow(17.0, 2)
        aRatio = aQb/aQt
        aL = 299.2239

        aA = afc/(aRatio -1)
        aC = math.acosh(aRatio)
        
        sketch = sketches.add(archComp.xYConstructionPlane, archOcc)
        
        # draw the top triangular section
        aH = math.sqrt(aQt * (1/math.tan(math.radians(30))))
        aH1 = (aH * 2.0) / 3.0
        aH2 = aH / 3.0
        aW = aH * math.tan(math.radians(30))

        aExtNeg = sketch.sketchPoints.add(adsk.core.Point3D.create(0.0, unitsManager.evaluateExpression("-{:.4f} ft".format(aW), "ft"), unitsManager.evaluateExpression("{:.4f} ft".format(afc + aH2), "ft")))
        aExtPos = sketch.sketchPoints.add(adsk.core.Point3D.create(0.0, unitsManager.evaluateExpression("{:.4f} ft".format(aW), "ft"), unitsManager.evaluateExpression("{:.4f} ft".format(afc + aH2), "ft")))
        aInt = sketch.sketchPoints.add(adsk.core.Point3D.create(0.0, 0.0, unitsManager.evaluateExpression("{:.4f} ft".format(afc - aH1), "ft")))

        crossSectionSketch = sketches.add(archComp.yZConstructionPlane, archOcc)
        csExtNeg = crossSectionSketch.project(aExtNeg).item(0)
        csExtPos = crossSectionSketch.project(aExtPos).item(0)
        csInt = crossSectionSketch.project(aInt).item(0)
        triangleCurves = adsk.core.ObjectCollection.create()
        triangleCurves.add(crossSectionSketch.sketchCurves.sketchLines.addByTwoPoints(csExtNeg, csExtPos))
        triangleCurves.add(crossSectionSketch.sketchCurves.sketchLines.addByTwoPoints(csExtPos, csInt))
        triangleCurves.add(crossSectionSketch.sketchCurves.sketchLines.addByTwoPoints(csInt, csExtNeg))
        loftProfile = crossSectionSketch.profiles.item(0)
        
        # create a sketch for the lip offset
        offsetSketch = sketches.add(archComp.yZConstructionPlane, archOcc)
        projectedTriangleCurves = offsetSketch.project(triangleCurves)
        triangleCurves.clear()
        offsetSketch.offset(projectedTriangleCurves, loftProfile.areaProperties(adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy).centroid, unitsManager.evaluateExpression("1.5 ft", "ft"))
        offsetSketch.offset(projectedTriangleCurves, loftProfile.areaProperties(adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy).centroid, unitsManager.evaluateExpression("3 ft", "ft"))
        for crv in projectedTriangleCurves:
            crv.deleteMe()
        
        for prf in offsetSketch.profiles:
            if prf.profileLoops.count == 2:
                lipProfile = prf
            if prf.profileLoops.count == 1:
                holeProfile = prf

        tolerance = unitsManager.evaluateExpression("1 in", "ft")

        lipFeature = None
        body = None
        n = 0
        for aX in xCoords:
            n = n + 1
            aY = aA*(math.cosh((aC*aX)/aL)-1)
            aEl = afc - aY
            aAngle = math.atan((aL / aC) * (1 / math.sqrt(2.0*aA*aY+aY*aY)))
            aQ = ((aQb - aQt) / afc) * aY + aQt
            aH = math.sqrt(aQ * (1/math.tan(math.radians(30))))
            aH1 = (aH * 2.0) / 3.0
            aH2 = aH / 3.0
            aExtX = aX + (aH2 * math.cos(aAngle))
            aExtY = aEl + (aH2 * math.sin(aAngle))
            aIntX = aX - (aH1 * math.cos(aAngle))
            aIntY = aEl - (aH1 * math.sin(aAngle))
            aW = aH * math.tan(math.radians(30))

            # determine the coordinates of the triangular cross-section
            aExtNeg = sketch.sketchPoints.add(adsk.core.Point3D.create(unitsManager.evaluateExpression("{:.4f} ft".format(aExtX), "ft"), unitsManager.evaluateExpression("-{:.4f} ft".format(aW), "ft"), unitsManager.evaluateExpression("{:.4f} ft".format(aExtY), "ft")))
            aExtPos = sketch.sketchPoints.add(adsk.core.Point3D.create(unitsManager.evaluateExpression("{:.4f} ft".format(aExtX), "ft"), unitsManager.evaluateExpression("{:.4f} ft".format(aW), "ft"), unitsManager.evaluateExpression("{:.4f} ft".format(aExtY), "ft")))
            aIntPoint = adsk.core.Point3D.create(unitsManager.evaluateExpression("{:.4f} ft".format(aIntX), "ft"), 0.0, unitsManager.evaluateExpression("{:.4f} ft".format(aIntY), "ft"))
            aInt = sketch.sketchPoints.add(aIntPoint)
            
            # create a sketch plane on the cross section
            planeInput = archComp.constructionPlanes.createInput(archOcc)
            planeInput.setByThreePoints(aExtNeg, aExtPos, aInt)
            crossSectionPlane = archComp.constructionPlanes.add(planeInput)
            
            # create a new sketch on the correct plane and add the new points to it
            crossSectionSketch = sketches.add(crossSectionPlane, archOcc)
            csExtNeg = crossSectionSketch.project(aExtNeg).item(0)
            csExtPos = crossSectionSketch.project(aExtPos).item(0)
            csInt = crossSectionSketch.project(aInt).item(0)

            # draw the edges of the cross section triangle
            triangleCurves.add(crossSectionSketch.sketchCurves.sketchLines.addByTwoPoints(csExtNeg, csExtPos))
            triangleCurves.add(crossSectionSketch.sketchCurves.sketchLines.addByTwoPoints(csExtPos, csInt))
            triangleCurves.add(crossSectionSketch.sketchCurves.sketchLines.addByTwoPoints(csInt, csExtNeg))
            previousLoftProfile = loftProfile
            loftProfile = crossSectionSketch.profiles.item(0)

            # create an offset triangle for the lip
            offsetSketch = sketches.add(crossSectionPlane, archOcc)
            projectedTriangleCurves = offsetSketch.project(triangleCurves)
            lipCurves = offsetSketch.offset(projectedTriangleCurves, loftProfile.areaProperties(adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy).centroid, unitsManager.evaluateExpression("1.5 ft", "ft"))
            notchSketch = sketches.add(crossSectionPlane, archOcc)
            
            notchProjectedTriangleCurves = notchSketch.project(triangleCurves)
            triangleCurves.clear()
            notchCurves = notchSketch.offset(notchProjectedTriangleCurves, loftProfile.areaProperties(adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy).centroid, unitsManager.evaluateExpression("1.4 ft", "ft"))
            notchSketch.project(notchCurves)
            for crv in notchProjectedTriangleCurves:
                crv.deleteMe()
            notchProfile = notchSketch.profiles.item(0)
            
            offsetSketch.offset(projectedTriangleCurves, loftProfile.areaProperties(adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy).centroid, unitsManager.evaluateExpression("3 ft", "ft"))
            for crv in projectedTriangleCurves:
                crv.deleteMe()
            previousLipProfile = lipProfile
            previousHoleProfile = holeProfile
            for prf in offsetSketch.profiles:
                if prf.profileLoops.count == 2:
                    lipProfile = prf
                if prf.profileLoops.count == 1:
                    holeProfile = prf

            # make a new component for the next section
            sectionOcc = archComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            sectionComp = sectionOcc.component
            sectionComp.name = "Section {}".format(n)

            # create the solid loft of the section
            featureInput = sectionComp.features.loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            featureInput.loftSections.add(previousLoftProfile)
            featureInput.loftSections.add(loftProfile)
            sectionLoftFeature = sectionComp.features.loftFeatures.add(featureInput)
            
            # create the notch
            featureInput = sectionComp.features.extrudeFeatures.createInput(notchProfile, adsk.fusion.FeatureOperations.CutFeatureOperation)
            featureInput.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('1.5 ft')), adsk.fusion.ExtentDirections.PositiveExtentDirection)
            sectionComp.features.extrudeFeatures.add(featureInput)
            
            # hollow out the interior
            featureInput = sectionComp.features.loftFeatures.createInput(adsk.fusion.FeatureOperations.CutFeatureOperation)
            featureInput.loftSections.add(previousHoleProfile)
            featureInput.loftSections.add(holeProfile)
            hollowCutFeature = sectionComp.features.loftFeatures.add(featureInput)

            # label the section
            labelFace = None
            for currentInteriorFace in hollowCutFeature.faces:
                if labelFace is None:
                    labelFace = currentInteriorFace
                else:
                    if currentInteriorFace.area > labelFace.area:
                        labelFace = currentInteriorFace
            sectionLabelSketch = sectionComp.sketches.add(labelFace)
            textSketchLine = None
            for currentSketchLine in sectionLabelSketch.sketchCurves.sketchLines:
                if textSketchLine is None:
                    textSketchLine = currentSketchLine
                else:
                    if currentSketchLine.length > textSketchLine.length:
                        textSketchLine = currentSketchLine
                        
            offsetTextSketchLine = sectionLabelSketch.offset(
                adsk.core.ObjectCollection.createWithArray([textSketchLine]), 
                sectionLabelSketch.profiles.item(0).areaProperties(adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy).centroid, 
                unitsManager.evaluateExpression("1 ft", "cm")
            )
            
            labelInput = sectionLabelSketch.sketchTexts.createInput2("{}".format(n), unitsManager.evaluateExpression("2 ft", "cm"))
            labelInput.setAsAlongPath(offsetTextSketchLine.item(0), False, adsk.core.HorizontalAlignments.CenterHorizontalAlignment, 0.0)
            labelInput.isHorizontalFlip = True
            labelInput.isVerticalFlip = True
            labelSketchText = sectionLabelSketch.sketchTexts.add(labelInput)

            labelTextExtrudeInput = sectionComp.features.extrudeFeatures.createInput(labelSketchText, adsk.fusion.FeatureOperations.CutFeatureOperation)
            labelTextExtrudeInput.setOneSideExtent(
                adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('0.2 ft')), 
                adsk.fusion.ExtentDirections.NegativeExtentDirection
            )
            sectionComp.features.extrudeFeatures.add(labelTextExtrudeInput)

            # create the lip
            featureInput = sectionComp.features.extrudeFeatures.createInput(previousLipProfile, adsk.fusion.FeatureOperations.JoinFeatureOperation)
            if lipFeature is None:
                direction = adsk.fusion.ExtentDirections.NegativeExtentDirection
            else:
                direction = adsk.fusion.ExtentDirections.PositiveExtentDirection    
            featureInput.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('1 ft')), direction)
            lipFeature = sectionComp.features.extrudeFeatures.add(featureInput)

    except:
        app.log(f'Failed:\n{traceback.format_exc()}')


def isEdgeOnPlane(edge: adsk.fusion.BRepEdge, plane: adsk.fusion.ConstructionPlane) -> bool:
    return isVertexOnPlane(edge.startVertex, plane) and isVertexOnPlane(edge.endVertex, plane)

def isVertexOnPlane(vertex: adsk.fusion.BRepVertex, plane: adsk.fusion.ConstructionPlane) -> bool:

    return plane.geometry.isCoPlanarTo(adsk.core.Plane.create(vertex.geometry, plane.geometry.normal))
