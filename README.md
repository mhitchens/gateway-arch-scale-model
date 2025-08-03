# gateway-arch-scale-model
An Autodesk Fusion script that generates the geometry of the Gateway Arch

I created this script as a sort of moonshot project idea after getting my first 3D printer. My goal was to create a scale model of the Gateway Arch by using the same engineering drawings and plans as the original, using Autodesk Fusion as the design tool.

Running this script in Fusion will create a component called "Gateway Arch", deleting a component with that name if it already exists. This script should be run after turning off design history for the design, as the code doesn't work well with that feature. I encourage someone to try an update it with parameteried geometry if possible.

The geometry created is actual size. I recommend setting the design's units to feet, as the original Arch plans are not in metric units, and the script deals in feet and inches.

Please feel free to open issues or send feedback.

The model has also been published to Printables at [https://www.printables.com/model/1374118-st-louis-gateway-arch-scale-model](https://www.printables.com/model/1374118-st-louis-gateway-arch-scale-model)
