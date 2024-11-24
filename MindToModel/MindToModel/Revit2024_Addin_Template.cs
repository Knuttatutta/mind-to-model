#region Namespaces
using System;
using System.Collections.Generic;
using System.Data.Common;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Windows.Forms.VisualStyles;
using System.Windows.Media.Imaging;
using System.Windows.Media.Media3D;
using Autodesk.Revit.ApplicationServices;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Selection;
using Newtonsoft.Json;
#endregion

namespace MindToModel
{
    public class CsAddRibbonButtons : IExternalApplication
    {
        public Result OnStartup(UIControlledApplication application)
        {
            // Create a custom ribbon tab
            string tabName = "MindToModel";
            application.CreateRibbonTab(tabName);

            // Create a custom ribbon panel
            RibbonPanel ribbonPanel = application.CreateRibbonPanel(tabName, "RibbonPanel1");

            string thisAssemblyPath = Assembly.GetExecutingAssembly().Location;

            // Create pushbutton
            PushButtonData buttonData = new PushButtonData("cmdCreateBuildingFromJsonCommand",
                   "Create Building From Json", thisAssemblyPath, "MindToModel.CreateBuildingFromJsonCommand");
            PushButton pushButton = ribbonPanel.AddItem(buttonData) as PushButton;

            // Add tooltip data to button
            pushButton.ToolTip = "Custom tooltip string";

            // Add icon to button
            string iconFilePath = @"C:\temp\Revit_addin_Icon_Example1.png";
            Uri uriImage = new Uri(iconFilePath);
            BitmapImage largeImage = new BitmapImage(uriImage);
            pushButton.LargeImage = largeImage;

            return Result.Succeeded;
        }

        public Result OnShutdown(UIControlledApplication application)
        {
            return Result.Succeeded;
        }
    }

    [Transaction(TransactionMode.Manual)]
    public class CreateBuildingFromJsonCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            Document doc = commandData.Application.ActiveUIDocument.Document;

            try
            {
                // Read the JSON input from a file
                string jsonInput = File.ReadAllText(@"C:\Users\mblijswijk\Desktop\Hackathon\241123 - AEC Hackathon Munich\building_geometry.json");
                //TaskDialog.Show("JSON", jsonInput.ToString());

                // Parse and process the JSON input
                var data = JsonConvert.DeserializeObject<BuildingData>(jsonInput);
                //TaskDialog.Show("JSON", JsonConvert.SerializeObject(data, Formatting.Indented).ToString());

                if (data == null)
                {
                    TaskDialog.Show("Error", "Invalid or unsuccessful JSON data.");
                    return Result.Failed;
                }

                List<double> levels_from_json_heights = new List<double>();
                foreach (var floorData in data.Components.Floors)
                {
                    levels_from_json_heights.Add(UnitUtils.ConvertToInternalUnits(floorData.Vertices[0].Z, UnitTypeId.Meters)); 
                }

                //List<double> elevations = new List<double> { 0.0, 3.0 * 3.28084, 6.0 * 3.28084, 9.0 * 3.28084 }; // Elevations in Revit internal units
                CreateLevels(doc, levels_from_json_heights);

                // Use a single transaction to create all walls and floors
                using (Transaction trans = new Transaction(doc, "Create Building Elements"))
                {
                    trans.Start();
                    int i = 0;
                    // Create Floors
                    foreach (var floorData in data.Components.Floors)
                    {
                        CreateFloor(doc, floorData, i);
                        // Create Walls
                        if (i == data.Components.Floors.Count - 1)
                        {
                            foreach (var wallData in data.Components.Walls)
                            {
                                CreateWall(doc, wallData, -1);
                            }
                        }
                        else {
                            foreach (var wallData in data.Components.Walls)
                            {
                                CreateWall(doc, wallData, i);
                            }
                        }
                        
                        i++;
                    }

                    // Get the default column type (FamilySymbol)
                    FamilySymbol defaultColumnType = new FilteredElementCollector(doc)
                        .OfClass(typeof(FamilySymbol))
                        .OfCategory(BuiltInCategory.OST_StructuralColumns)
                        .FirstOrDefault() as FamilySymbol;

                    if (defaultColumnType == null)
                    {
                        throw new InvalidOperationException("No structural column family types found in the document.");
                    }

                    // Get a level from the document (replace with a specific level if needed)
                    Level level = new FilteredElementCollector(doc)
                        .OfClass(typeof(Level))
                        .FirstOrDefault() as Level;

                    if (level == null)
                    {
                        throw new InvalidOperationException("No levels found in the document.");
                    }

                    // Deserialize columns from JSON
                    List<ColumnData> columns = data.Components.Columns; // Replace with your deserialization logic

                    // Use the default column type
                    CreateColumnsFromData(doc, columns, defaultColumnType.Id, level);

                    //foreach (var col in data.Components.beams)
                    //{
                    //    CreateBeams(Document doc, List < Beam > beams, Level level)
                    //}


                    trans.Commit();
                }

                CreateOpeningsFromJson(doc, data.Components.Openings);

                TaskDialog.Show("Success", "Building elements created successfully.");
                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                TaskDialog.Show("Error", $"An error occurred: {ex.Message}");
                return Result.Failed;
            }
        }


        private void CreateWall(Document doc, WallData wallData, int iter)
        {
            // Check if the wall type exists
            if (wallData.Id.Contains("penthouse"))
            {
                if (iter == -1)
                {
                    TaskDialog.Show("penthouse", "penthouse");

                    List<XYZ> points = new List<XYZ>();
                    foreach (var vertex in wallData.Vertices)
                    {
                        points.Add(new XYZ(
                            UnitUtils.ConvertToInternalUnits(vertex.X, UnitTypeId.Meters),
                            UnitUtils.ConvertToInternalUnits(vertex.Y, UnitTypeId.Meters),
                            UnitUtils.ConvertToInternalUnits(vertex.Z, UnitTypeId.Meters)
                            ));
                    }

                    List<Curve> curves = new List<Curve>();
                    Level baseLevel = new FilteredElementCollector(doc)
                        .OfClass(typeof(Level))
                        .Cast<Level>()
                        .OrderByDescending(l => l.Elevation)
                        .Skip(1)
                        .FirstOrDefault();
                    ElementId defaultWallTypeId = new FilteredElementCollector(doc).OfClass(typeof(WallType)).FirstElementId();

                    for (int i = 0; i < points.Count; i++)
                    {
                        XYZ start = points[i];
                        XYZ end = points[(i + 1) % points.Count];  // Loop back to the first point
                        curves.Add(Line.CreateBound(start, end));  // Add the line to the List<Curve>
                    }

                    Wall wall = Wall.Create(doc, curves, defaultWallTypeId, baseLevel.Id, false);
                    Parameter heightParam = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM);
                    if (heightParam != null)
                    {
                        heightParam.Set(UnitUtils.ConvertToInternalUnits(2.7, UnitTypeId.Meters));
                    }



                    // Set the location line to "Finish Face: Exterior"
                    LocationCurve locationCurve = wall.Location as LocationCurve;
                    wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(2);

                    // Get the wall type by name (assuming "Wall 200mm" is the wall type's name)
                    WallType wallType = GetWallTypeByName(doc, "Wall 200mm");

                    // Check if the wall type exists
                    if (wallType == null)
                    {
                        TaskDialog.Show("Error", "Wall type 'Wall 200mm' not found.");
                        return;
                    }

                    // Set the wall's type to "Wall 200mm"
                    wall.WallType = wallType;

                }

                return;
            }
            else {
                List<XYZ> points = new List<XYZ>();
                foreach (var vertex in wallData.Vertices)
                {
                    points.Add(new XYZ(
                            UnitUtils.ConvertToInternalUnits(vertex.X, UnitTypeId.Meters),
                            UnitUtils.ConvertToInternalUnits(vertex.Y, UnitTypeId.Meters),
                            UnitUtils.ConvertToInternalUnits(vertex.Z, UnitTypeId.Meters)
                            ));
                }

                List<Curve> curves = new List<Curve>();
                Level baseLevel = GetLevelByName(doc, $"Level {iter}") ?? CreateDefaultLevel(doc);
                ElementId defaultWallTypeId = new FilteredElementCollector(doc).OfClass(typeof(WallType)).FirstElementId();

                for (int i = 0; i < points.Count; i++)
                {
                    XYZ start = points[i];
                    XYZ end = points[(i + 1) % points.Count];  // Loop back to the first point
                    curves.Add(Line.CreateBound(start, end));  // Add the line to the List<Curve>
                }

                Wall wall = Wall.Create(doc, curves, defaultWallTypeId, baseLevel.Id, false);
                Parameter heightParam = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM);
                if (heightParam != null)
                {
                    heightParam.Set(UnitUtils.ConvertToInternalUnits(2.7, UnitTypeId.Meters));
                }



                // Set the location line to "Finish Face: Exterior"
                LocationCurve locationCurve = wall.Location as LocationCurve;
                wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(2);

                // Get the wall type by name (assuming "Wall 200mm" is the wall type's name)
                WallType wallType = GetWallTypeByName(doc, "Wall 200mm");

                // Check if the wall type exists
                if (wallType == null)
                {
                    TaskDialog.Show("Error", "Wall type 'Wall 200mm' not found.");
                    return;
                }

                // Set the wall's type to "Wall 200mm"
                wall.WallType = wallType;
            }

            

        }

        public WallType GetWallTypeByName(Document doc, string wallTypeName)
        {
            // Get all wall types in the document
            FilteredElementCollector collector = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType));  // Collect all WallType elements

            // Find the wall type by name
            foreach (WallType wallType in collector)
            {
                if (wallType.Name == wallTypeName)
                {
                    return wallType;
                }
            }

            // Return null if not found
            return null;
        }


        private void CreateFloor(Document doc, FloorData floorData, int iter)
        {
            List<XYZ> points = new List<XYZ>();
            foreach (var vertex in floorData.Vertices)
            {
                points.Add(new XYZ(
                            UnitUtils.ConvertToInternalUnits(vertex.X, UnitTypeId.Meters),
                            UnitUtils.ConvertToInternalUnits(vertex.Y, UnitTypeId.Meters),
                            UnitUtils.ConvertToInternalUnits(vertex.Z, UnitTypeId.Meters)
                            ));
            }

            List<CurveLoop> curveLoops = new List<CurveLoop>();
            CurveLoop curveLoop = new CurveLoop();

            for (int i = 0; i < points.Count; i++)
            {
                XYZ start = points[i];
                XYZ end = points[(i + 1) % points.Count];
                curveLoop.Append(Line.CreateBound(start, end));
            }

            List<CurveLoop> newCurveLoops = new List<CurveLoop>();
            curveLoops.Add(curveLoop);

            ElementId floorTypeId = Floor.GetDefaultFloorType(doc, false);
            Level level = GetLevelByName(doc, $"Level {iter}") ?? CreateDefaultLevel(doc);
            ElementId levelId = level.Id;

            

            foreach (CurveLoop curveLoop1 in curveLoops)
            {
                // Offset the current loop
                CurveLoop offsetLoop = CurveLoop.CreateViaOffset(curveLoop1, UnitUtils.ConvertToInternalUnits(0.1, UnitTypeId.Meters), XYZ.BasisZ);
                newCurveLoops.Add(offsetLoop);
            }

            Floor newFloor = Floor.Create(doc, newCurveLoops, floorTypeId, levelId);
        }

        private Level GetLevelByName(Document doc, string name)
        {
            FilteredElementCollector collector = new FilteredElementCollector(doc)
                .OfClass(typeof(Level));
            foreach (Element e in collector)
            {
                if (e.Name == name)
                {
                    return e as Level;
                }
            }
            return null;
        }

        private Level CreateDefaultLevel(Document doc)
        {
            return Level.Create(doc, 0);
        }

        private Level CreateNewLevel(Document doc, int num)
        {
            return Level.Create(doc, num);
        }

        public void CreateLevels(Document doc, List<double> elevations)
        {
            // Ensure the document is not null
            if (doc == null)
            {
                throw new System.ArgumentNullException(nameof(doc));
            }

            // Start a transaction to create levels
            using (Transaction trans = new Transaction(doc, "Create Levels"))
            {
                trans.Start();
                int i = 1;
                foreach (double elevation in elevations)
                {
                    
                    // Create a new level at the given elevation
                    Level level = Level.Create(doc, elevation);

                    // Optionally set a name for the level
                    level.Name = $"Level {i}";

                    // Ensure the level is created successfully
                    if (level == null)
                    {
                        throw new System.InvalidOperationException($"Failed to create level at elevation {elevation}.");
                    }
                    i++;
                }

                // Commit the transaction
                trans.Commit();
            }

        }

        public static void CreateBeams(Document doc, List<Beam> beams, Level level, ElementId beamTypeId=null)
        {
            using (Transaction trans = new Transaction(doc, "Create Beams"))
            {
                trans.Start();

                foreach (var beam in beams)
                {
                    XYZ start = new XYZ(beam.StartPoint.X, beam.StartPoint.Y, beam.StartPoint.Z);
                    XYZ end = new XYZ(beam.EndPoint.X, beam.EndPoint.Y, beam.EndPoint.Z);

                    FamilySymbol beamType = doc.GetElement(beamTypeId) as FamilySymbol;

                    if (beamType != null && !beamType.IsActive)
                    {
                        beamType.Activate(); // Ensure the FamilySymbol is active
                        doc.Regenerate();
                    }

                    FamilyInstance beamInstance = doc.Create.NewFamilyInstance(Line.CreateBound(start, end),
                        beamType, level, StructuralType.Beam);

                    // Optionally set a name or parameter for the beam
                    Parameter idParam = beamInstance.LookupParameter("BeamId");
                    if (idParam != null && idParam.IsReadOnly == false)
                    {
                        idParam.Set(beam.Id);
                    }
                }

                trans.Commit();
            }
        }

        public void CreateColumnsFromData(Document doc, List<ColumnData> columns, ElementId columnTypeId, Level level)
        {
            // Get the column family type (FamilySymbol) from the provided ElementId
            FamilySymbol columnType = doc.GetElement(columnTypeId) as FamilySymbol;

            if (columnType == null)
            {
                throw new ArgumentException("Invalid columnTypeId provided.");
            }

            // Ensure the column type is active
            if (!columnType.IsActive)
            {
                columnType.Activate();
                doc.Regenerate();
            }

            foreach (var column in columns)
            {
                // Create the start and end points of the column
                XYZ start = new XYZ(
                    UnitUtils.ConvertToInternalUnits(column.StartPoint.X, UnitTypeId.Meters),
                    UnitUtils.ConvertToInternalUnits(column.StartPoint.Y, UnitTypeId.Meters),
                    UnitUtils.ConvertToInternalUnits(column.StartPoint.Z, UnitTypeId.Meters)
                    );
                XYZ end = new XYZ(
                    UnitUtils.ConvertToInternalUnits(column.EndPoint.X, UnitTypeId.Meters),
                    UnitUtils.ConvertToInternalUnits(column.EndPoint.Y, UnitTypeId.Meters),
                    UnitUtils.ConvertToInternalUnits(column.EndPoint.Z, UnitTypeId.Meters)
                    );

                // Create the column
                FamilyInstance columnInstance = doc.Create.NewFamilyInstance(Line.CreateBound(start, end),
                    columnType, level, StructuralType.Column);


            }
        }

        public void CreateOpeningsFromJson(Document doc, List<OpeningData> openings)
        {
            using (Transaction trans = new Transaction(doc, "Create Openings"))
            {
                trans.Start();

                // Get the FamilySymbols for windows and doors (if they exist in the project)
                FamilySymbol windowType = new FilteredElementCollector(doc)
                    .OfClass(typeof(FamilySymbol))
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .FirstOrDefault() as FamilySymbol;

                FamilySymbol doorType = new FilteredElementCollector(doc)
                    .OfClass(typeof(FamilySymbol))
                    .OfCategory(BuiltInCategory.OST_Doors)
                    .FirstOrDefault() as FamilySymbol;

                if (windowType == null && doorType == null)
                {
                    TaskDialog.Show("Error", "No window or door types found.");
                    return;
                }

                // Process each opening
                foreach (var opening in openings)
                {
                    // Determine opening type (window or door)
                    FamilySymbol openingType = (opening.type == "window") ? windowType : doorType;

                    if (openingType == null)
                        continue; // Skip if the type is invalid

                    // Activate the FamilySymbol if it's not already active
                    if (!openingType.IsActive)
                    {
                        openingType.Activate();
                        doc.Regenerate();
                    }

                    // Convert the XYZ coordinates from meters to internal units (Revit uses feet)
                    XYZ startPoint = new XYZ(
                        UnitUtils.ConvertToInternalUnits(opening.vertices[0].X, UnitTypeId.Meters),
                        UnitUtils.ConvertToInternalUnits(opening.vertices[0].Y, UnitTypeId.Meters),
                        UnitUtils.ConvertToInternalUnits(opening.vertices[0].Z, UnitTypeId.Meters)
                    );

                    XYZ endPoint = new XYZ(
                        UnitUtils.ConvertToInternalUnits(opening.vertices[2].X, UnitTypeId.Meters),
                        UnitUtils.ConvertToInternalUnits(opening.vertices[2].Y, UnitTypeId.Meters),
                        UnitUtils.ConvertToInternalUnits(opening.vertices[2].Z, UnitTypeId.Meters)
                    );

                    // Use the midpoint for the location of the opening
                    XYZ location = new XYZ(
                        (startPoint.X + endPoint.X) / 2,
                        (startPoint.Y + endPoint.Y) / 2,
                        (startPoint.Z + endPoint.Z) / 2
                    );

                    // Find the wall where the opening should be created (you can refine this part to fit your needs)
                    Wall wall = FindWallAtLocation(doc, location);
                    if (wall == null)
                    {
                        TaskDialog.Show("Error", "No wall found for opening placement.");
                        continue;
                    }

                    // Find the wall face (this is critical for proper placement)
                    ElementId wallId = wall.Id;
                    LocationCurve locationCurve = wall.Location as LocationCurve;
                    if (locationCurve == null)
                        continue; // Skip if wall has no location curve (shouldn't happen)

                    // Get the correct wall face (we will assume front face for now)
                    Line line = locationCurve.Curve as Line;
                    if (line == null)
                        continue;

                    XYZ wallNormal = line.Direction.CrossProduct(XYZ.BasisZ); // Get the normal to the wall

                    // Determine the placement location based on the wall normal
                    XYZ openingPosition = location + wallNormal * 0.5; // Offset the opening by 0.5 to ensure it's placed correctly


                    try
                    {
                        // Place the window or door (FamilyInstance)
                        FamilyInstance openingInstance = doc.Create.NewFamilyInstance(openingPosition, openingType, wall, StructuralType.NonStructural);
                    }
                    catch
                    { 
                        
                    }

                    
                }

                trans.Commit();
            }
        }


        private Wall FindWallAtLocation(Document doc, XYZ location)
        {
            // Simple method to find the closest wall to the specified location
            var walls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .ToList();

            Wall closestWall = null;
            double closestDistance = double.MaxValue;

            foreach (var wall in walls)
            {
                LocationCurve locationCurve = wall.Location as LocationCurve;
                
                if (locationCurve != null)
                {
                    Curve wallCurve = locationCurve.Curve;
                    double distance = wallCurve.Distance(location);
                    if (distance < closestDistance)
                    {
                        closestDistance = distance;
                        closestWall = wall;
                    }
                }
            }

            return closestWall;
        }
    }

    public class BuildingData
    {
        public string BuildingId { get; set; } // Matches "buildingId" in JSON
        public Components Components { get; set; }
        public string Units { get; set; } // Matches "units" in JSON
    }

    public class Components
    {
        public List<WallData> Walls { get; set; }
        public List<FloorData> Floors { get; set; }
        public List<ColumnData> Columns { get; set; }
        public List<OpeningData> Openings { get; set; }
    }

    public class WallData
    {
        public string Id { get; set; } // Matches "id" in JSON
        public List<Vertex> Vertices { get; set; } // Matches "vertices" in JSON
    }

    public class FloorData
    {
        public string Id { get; set; } // Matches "id" in JSON
        public List<Vertex> Vertices { get; set; } // Matches "vertices" in JSON
    }

    public class Vertex
    {
        public double X { get; set; } // Matches "x" in JSON
        public double Y { get; set; } // Matches "y" in JSON
        public double Z { get; set; } // Matches "z" in JSON
    }

    public class Beam
    {
        public string Id { get; set; }
        public Vertex StartPoint { get; set; }
        public Vertex EndPoint { get; set; }
    }

    public class ColumnData
    {
        public string Id { get; set; }
        public Vertex StartPoint { get; set; }
        public Vertex EndPoint { get; set; }
    }

    public class OpeningData
    {
        public string id { get; set; }
        public string type { get; set; }  // "window" or "door"
        public List<Vertex> vertices { get; set; }
    }


}




//using Autodesk.Revit.ApplicationServices;
//using Autodesk.Revit.Attributes;
//using Autodesk.Revit.DB;
//using Autodesk.Revit.DB.Structure;
//using Autodesk.Revit.UI;
//using Microsoft.Win32;
//using Newtonsoft.Json;
//using System;
//using System.Collections.Generic;
//using System.IO;
//using System.Linq;
//using System.Reflection;
//using System.Windows.Media.Imaging;
//using System.Windows.Forms;
//using MindToModel;

//namespace MindToModel
//{


//    // Building data classes to match JSON structure
//    public class BuildingData
//    {
//        public string BuildingId { get; set; }
//        public Components Components { get; set; }
//        public string Units { get; set; }
//    }

//    public class Components
//    {
//        public List<Wall> Walls { get; set; }
//        public List<Floor> Floors { get; set; }
//        public List<Opening> Openings { get; set; }
//        public List<Column> Columns { get; set; }
//        public List<Beam> Beams { get; set; }
//    }

//    public class Vertex
//    {
//        public double X { get; set; }
//        public double Y { get; set; }
//        public double Z { get; set; }
//    }

//    public class Wall
//    {
//        public string Id { get; set; }
//        public List<Vertex> Vertices { get; set; }
//    }

//    public class Floor
//    {
//        public string Id { get; set; }
//        public List<Vertex> Vertices { get; set; }
//    }

//    public class Opening
//    {
//        public string Id { get; set; }
//        public string Type { get; set; }
//        public List<Vertex> Vertices { get; set; }
//    }

//    public class Column
//    {
//        public string Id { get; set; }
//        public Vertex StartPoint { get; set; }
//        public Vertex EndPoint { get; set; }
//    }

//    public class Beam
//    {
//        public string Id { get; set; }
//        public Vertex StartPoint { get; set; }
//        public Vertex EndPoint { get; set; }
//    }

//    [Transaction(TransactionMode.Manual)]
//    public class BuildingModelCommand : IExternalCommand
//    {
//        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
//        {
//            UIApplication uiapp = commandData.Application;
//            UIDocument uidoc = uiapp.ActiveUIDocument;
//            Document doc = uidoc.Document;
//            System.Windows.Forms.Form form = new System.Windows.Forms.Form();
//            form.TopMost = true;
//            try
//            {
//                OpenFileDialog openFileDialog = new OpenFileDialog
//                {
//                    Filter = "JSON files (*.json)|*.json|All files (*.*)|*.*",
//                    Title = "Select Building JSON File",
//                    InitialDirectory = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments)
//                };
//                if (openFileDialog.ShowDialog(form) == DialogResult.OK)
//                {
//                    // Read and parse JSON
//                    string jsonContent = File.ReadAllText(openFileDialog.FileName);
//                    TaskDialog.Show("Debug", $"JSON Content Length: {jsonContent.Length}");
//                    BuildingData buildingData = JsonConvert.DeserializeObject<BuildingData>(jsonContent);
//                    if (buildingData == null)
//                    {
//                        TaskDialog.Show("Error", "Failed to parse JSON data");
//                        return Result.Failed;
//                    }
//                    // Validate building data
//                    string validationMessage = ValidateBuildingData(buildingData);
//                    if (!string.IsNullOrEmpty(validationMessage))
//                    {
//                        TaskDialog.Show("Validation Error", validationMessage);
//                        return Result.Failed;
//                    }
//                    using (Transaction trans = new Transaction(doc, "Create Building Model"))
//                    {
//                        trans.Start();
//                        try
//                        {
//                            // Get default level
//                            Level level = new FilteredElementCollector(doc)
//                                .OfClass(typeof(Level))
//                                .FirstElement() as Level;
//                            if (level == null)
//                            {
//                                TaskDialog.Show("Error", "No levels found in project");
//                                return Result.Failed;
//                            }
//                            int elementCount = 0;
//                            // Create Walls
//                            if (buildingData.Components?.Walls != null && buildingData.Components.Walls.Any())
//                            {
//                                elementCount += CreateWalls(doc, buildingData.Components.Walls, level);
//                                TaskDialog.Show("Debug", $"Created {elementCount} walls");
//                            }
//                            // Create Floors
//                            if (buildingData.Components?.Floors != null && buildingData.Components.Floors.Any())
//                            {
//                                elementCount += CreateFloors(doc, buildingData.Components.Floors, level);
//                                TaskDialog.Show("Debug", $"Created floors, total elements: {elementCount}");
//                            }
//                            // Create Openings
//                            if (buildingData.Components?.Openings != null && buildingData.Components.Openings.Any())
//                            {
//                                elementCount += CreateOpenings(doc, buildingData.Components.Openings, level);
//                                TaskDialog.Show("Debug", $"Created openings, total elements: {elementCount}");
//                            }
//                            // Create Columns
//                            if (buildingData.Components?.Columns != null && buildingData.Components.Columns.Any())
//                            {
//                                elementCount += CreateColumns(doc, buildingData.Components.Columns, level);
//                                TaskDialog.Show("Debug", $"Created columns, total elements: {elementCount}");
//                            }
//                            // Create Beams
//                            if (buildingData.Components?.Beams != null && buildingData.Components.Beams.Any())
//                            {
//                                elementCount += CreateBeams(doc, buildingData.Components.Beams, level);
//                                TaskDialog.Show("Debug", $"Created beams, total elements: {elementCount}");
//                            }
//                            trans.Commit();
//                            if (elementCount > 0)
//                            {
//                                TaskDialog.Show("Success", $"Successfully created {elementCount} building elements");
//                                return Result.Succeeded;
//                            }
//                            else
//                            {
//                                TaskDialog.Show("Warning", "No elements were created. Check your JSON data.");
//                                return Result.Failed;
//                            }
//                        }
//                        catch (Exception ex)
//                        {
//                            trans.RollBack();
//                            throw new Exception($"Error during element creation: {ex.Message}");
//                        }
//                    }
//                }
//                return Result.Cancelled;
//            }
//            catch (Exception ex)
//            {
//                message = ex.Message;
//                TaskDialog.Show("Error", $"An error occurred: {ex.Message}\n\nStack Trace:\n{ex.StackTrace}");
//                return Result.Failed;
//            }
//            finally
//            {
//                form.Dispose();
//            }
//        }
//        private string ValidateBuildingData(BuildingData data)
//        {
//            if (data == null) return "Building data is null";
//            if (data.Components == null) return "No components found in building data";
//            List<string> errors = new List<string>();
//            if (data.Components.Walls != null)
//            {
//                foreach (var wall in data.Components.Walls)
//                {
//                    if (wall.Vertices == null || wall.Vertices.Count != 2)
//                        errors.Add($"Wall {wall.Id}: Invalid vertices count");
//                }
//            }
//            if (data.Components.Floors != null)
//            {
//                foreach (var floor in data.Components.Floors)
//                {
//                    if (floor.Vertices == null || floor.Vertices.Count < 3)
//                        errors.Add($"Floor {floor.Id}: Invalid vertices count");
//                }
//            }
//            return errors.Any() ? string.Join("\n", errors) : string.Empty;
//        }
//        private int CreateWalls(Document doc, List<Wall> walls, Level level)
//        {
//            int count = 0;
//            WallType wallType = new FilteredElementCollector(doc)
//                .OfClass(typeof(WallType))
//                .FirstElement() as WallType;
//            if (wallType == null)
//            {
//                TaskDialog.Show("Error", "No wall type found in project");
//                return 0;
//            }
//            foreach (var wall in walls)
//            {
//                try
//                {
//                    XYZ start = ConvertToFeet(wall.Vertices[0]);
//                    XYZ end = ConvertToFeet(wall.Vertices[1]);
//                    // Check if points are valid
//                    if (start.DistanceTo(end) < 0.1)
//                    {
//                        TaskDialog.Show("Warning", $"Wall {wall.Id} is too short, skipping");
//                        continue;
//                    }
//                    Line wallLine = Line.CreateBound(start, end);
//                    Autodesk.Revit.DB.Wall revitWall = Autodesk.Revit.DB.Wall.Create(
//                        doc,
//                        wallLine,
//                        wallType.Id,
//                        level.Id,
//                        10.0, // height in feet
//                        0.0,  // offset
//                        false, // flip
//                        true  // structural
//                    );
//                    if (revitWall != null)
//                    {
//                        Parameter markParam = revitWall.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
//                        if (markParam != null)
//                            markParam.Set(wall.Id);
//                        count++;
//                    }
//                }
//                catch (Exception ex)
//                {
//                    TaskDialog.Show("Wall Creation Error", $"Error creating wall {wall.Id}: {ex.Message}");
//                }
//            }
//            return count;
//        }
//        // Similar modifications for CreateFloors, CreateOpenings, CreateColumns, and CreateBeams
//        // Add error checking and return count of created elements
//        private XYZ ConvertToFeet(Vertex vertex)
//        {
//            double factor = 3.28084; // meters to feet
//            return new XYZ(
//                vertex.X * factor,
//                vertex.Y * factor,
//                vertex.Z * factor
//            );
//        }


//        private void CreateFloors(Document doc, List<Floor> floors, Level level)
//        {
//            if (floors == null) return;
//            // Get default floor type
//            FloorType floorType = new FilteredElementCollector(doc)
//                .OfClass(typeof(FloorType))
//                .FirstElement() as FloorType;
//            foreach (var floor in floors)
//            {
//                try
//                {
//                    // Create profile points
//                    List<XYZ> points = floor.Vertices.Select(v => ConvertToFeet(v)).ToList();
//                    points.Add(points[0]); // Close the loop
//                                           // Create curve array
//                    CurveArray curves = new CurveArray();
//                    for (int i = 0; i < points.Count - 1; i++)
//                    {
//                        curves.Append(Line.CreateBound(points[i], points[i + 1]));
//                    }
//                    // Create curve loops for floor creation
//                    List<CurveLoop> curveLoops = new List<CurveLoop>();
//                    CurveLoop curveLoop = new CurveLoop();
//                    foreach (Curve curve in curves)
//                    {
//                        curveLoop.Append(curve);
//                    }
//                    curveLoops.Add(curveLoop);
//                    // Create floor
//                    Autodesk.Revit.DB.Floor revitFloor = Autodesk.Revit.DB.Floor.Create(
//                        doc,
//                        curveLoops,
//                        floorType.Id,
//                        level.Id);
//                    if (revitFloor != null)
//                    {
//                        Parameter markParam = revitFloor.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
//                        if (markParam != null)
//                            markParam.Set(floor.Id);
//                    }
//                }
//                catch (Exception ex)
//                {
//                    TaskDialog.Show("Floor Creation Error",
//                        $"Error creating floor {floor.Id}: {ex.Message}");
//                }
//            }
//        }

//        private void CreateOpenings(Document doc, List<Opening> openings, Level level)
//        {
//            if (openings == null) return;

//            // Get default door and window types
//            FamilySymbol doorType = new FilteredElementCollector(doc)
//                .OfClass(typeof(FamilySymbol))
//                .OfCategory(BuiltInCategory.OST_Doors)
//                .FirstElement() as FamilySymbol;

//            FamilySymbol windowType = new FilteredElementCollector(doc)
//                .OfClass(typeof(FamilySymbol))
//                .OfCategory(BuiltInCategory.OST_Windows)
//                .FirstElement() as FamilySymbol;

//            if (!doorType.IsActive) doorType.Activate();
//            if (!windowType.IsActive) windowType.Activate();

//            foreach (var opening in openings)
//            {
//                // Calculate center point
//                XYZ center = ConvertToFeet(new Vertex
//                {
//                    X = opening.Vertices.Average(v => v.X),
//                    Y = opening.Vertices.Average(v => v.Y),
//                    Z = opening.Vertices.Average(v => v.Z)
//                });

//                // Find closest wall
//                Autodesk.Revit.DB.Wall hostWall = FindClosestWall(doc, center);
//                if (hostWall == null) continue;

//                FamilyInstance instance = doc.Create.NewFamilyInstance(
//                    center,
//                    opening.Type.ToLower() == "door" ? doorType : windowType,
//                    hostWall,
//                    level,
//                    StructuralType.NonStructural);

//                if (instance != null)
//                {
//                    Parameter markParam = instance.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
//                    if (markParam != null)
//                        markParam.Set(opening.Id);
//                }
//            }
//        }

//        private void CreateColumns(Document doc, List<Column> columns, Level level)
//        {
//            if (columns == null) return;

//            // Get default column type
//            FamilySymbol columnType = new FilteredElementCollector(doc)
//                .OfClass(typeof(FamilySymbol))
//                .OfCategory(BuiltInCategory.OST_Columns)
//                .FirstElement() as FamilySymbol;

//            if (!columnType.IsActive) columnType.Activate();

//            foreach (var column in columns)
//            {
//                XYZ basePoint = ConvertToFeet(column.StartPoint);
//                XYZ topPoint = ConvertToFeet(column.EndPoint);

//                FamilyInstance instance = doc.Create.NewFamilyInstance(
//                    basePoint,
//                    columnType,
//                    level,
//                    StructuralType.Column);

//                if (instance != null)
//                {
//                    Parameter markParam = instance.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
//                    if (markParam != null)
//                        markParam.Set(column.Id);

//                    Parameter heightParam = instance.get_Parameter(BuiltInParameter.INSTANCE_LENGTH_PARAM);
//                    if (heightParam != null)
//                        heightParam.Set(basePoint.DistanceTo(topPoint));
//                }
//            }
//        }

//        private void CreateBeams(Document doc, List<Beam> beams, Level level)
//        {
//            if (beams == null) return;

//            // Get default beam type
//            FamilySymbol beamType = new FilteredElementCollector(doc)
//                .OfClass(typeof(FamilySymbol))
//                .OfCategory(BuiltInCategory.OST_StructuralFraming)
//                .FirstElement() as FamilySymbol;

//            if (!beamType.IsActive) beamType.Activate();

//            foreach (var beam in beams)
//            {
//                XYZ startPoint = ConvertToFeet(beam.StartPoint);
//                XYZ endPoint = ConvertToFeet(beam.EndPoint);
//                Line beamLine = Line.CreateBound(startPoint, endPoint);

//                FamilyInstance instance = doc.Create.NewFamilyInstance(
//                    beamLine,
//                    beamType,
//                    level,
//                    StructuralType.Beam);

//                if (instance != null)
//                {
//                    Parameter markParam = instance.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
//                    if (markParam != null)
//                        markParam.Set(beam.Id);
//                }
//            }
//        }

//        private XYZ ConvertToFeet(Vertex vertex)
//        {
//            // Convert from meters to feet
//            double factor = 3.28084;
//            return new XYZ(
//                vertex.X * factor,
//                vertex.Y * factor,
//                vertex.Z * factor);
//        }

//        private Autodesk.Revit.DB.Wall FindClosestWall(Document doc, XYZ point)
//        {
//            FilteredElementCollector wallCollector = new FilteredElementCollector(doc)
//                .OfClass(typeof(Autodesk.Revit.DB.Wall));
//            Autodesk.Revit.DB.Wall closestWall = null;
//            double minDistance = double.MaxValue;
//            foreach (Autodesk.Revit.DB.Wall wall in wallCollector)
//            {
//                LocationCurve locationCurve = wall.Location as LocationCurve;
//                if (locationCurve != null)
//                {
//                    Curve curve = locationCurve.Curve;
//                    double distance = curve.Distance(point);
//                    if (distance < minDistance)
//                    {
//                        minDistance = distance;
//                        closestWall = wall;
//                    }
//                }
//            }
//            return closestWall;
//        }
//    }

//    public class CsAddRibbonButtons : IExternalApplication
//    {
//        public Result OnStartup(UIControlledApplication application)
//        {
//            // Create ribbon tab
//            string tabName = "MindToModel";
//            application.CreateRibbonTab(tabName);

//            // Create ribbon panel
//            RibbonPanel ribbonPanel = application.CreateRibbonPanel(tabName, "Tools");

//            // Create button
//            string thisAssemblyPath = Assembly.GetExecutingAssembly().Location;
//            PushButtonData buttonData = new PushButtonData(
//                "BuildingModelCreator",
//                "Create\nModel",
//                thisAssemblyPath,
//                "MindToModel.BuildingModelCommand")
//            {
//                ToolTip = "Create building model from JSON file",
//                //LargeImage = new BitmapImage(new Uri("pack://application:,,,/BuildingModelCreator;component/Resources/icon.png"))
//            };

//            ribbonPanel.AddItem(buttonData);

//            return Result.Succeeded;
//        }

//        public Result OnShutdown(UIControlledApplication application)
//        {
//            return Result.Succeeded;
//        }
//    }
//}















