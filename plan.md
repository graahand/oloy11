# checklist
- [ ] first I need a class diagram and pseudocode to the entire code required to be written for this project along with a very simply description (points based) as a official document to know about the project. 
- [ ] swagger API as the way to test the APIs no UI required.
- [ ] Complete the below given tasks in order and there should be trace of the steps that were followed while writing the code base, there should be comments, numbers anything that will allow me to know which code is written when and commenting which code will disable which of the API. Currently
- [ ] Complete the first 8 tasks only for now, each individual APIs, 
- [ ] Follow the given below python practice for the code written
- [ ] Redundancy is strictly prohibited.
- [ ] Also list out the required tests before working on the API development. 
- [ ] Pydantic for data validation, define Pydantic data models with the required attributes and their corresponding types. 
- [ ] Implementation of path and query parameters (use where this is possible to be implemented)
- [ ] Focus on Maintainability and Scalibity along with Knowledge Transfer for someone learning the whereabouts about working with FastAPI. 
- [ ] File for tracking the version of the project (semantic versioning is preferred). 

## main theme
A fastapi based backend development which have following features in order to be implemented. 
1. image upload (should be able to provide image via url as well)
2. loading model and running inference
3. image preprocessing pipeline (resize and other yolo supported pre-processing steps)
4. tweaking yolo object detection model's and instance segmentation model's arguments (conf, iou, max_det, agnostic_nms)
5. video upload with video's preprocessing (list them out)
6. inference on video and wrapping the video's results informatively
7. login and registration 
8. user history
9. logout 
10. admin dashboard
11. CRUD operations


## python practices which requires to be met: 
1. add the entry point to the exectuble script. if you are running any python file then create the main entry point at the end of the file. 
   `if __name__ == 'main':
   `main`
2. Simplify the function as much as you can't don't overcomplicate the function with multiple functionality, also add the return type for the function while defining the function. 
3. if the python file have multiple functions then create a main function at the end of the python file and then add the main entry point after that main function to run that main function where required functions are being called. 
4. explicitly add the data type for the variable: `number: int = 19` (type annotation)
5. use list comprehension if it can be implemented anywhere in the code. 
6. iterate with enumerate instead of range object, enumerate gives both index and element.  
7. store unique values with set. 
8. Use singleton instance for class such as a Model loading from hugging face or any external API such as PaddleOCR, EasyOCR
9. use of abstract base class
10. Modular architecture 
11. A central controller file that orchestrates, initializes and manages all individual checker components. 
12. write the validation rules as the data structures instead of the hard-coded logic. 
13. Use of pathlib to work with the files and directories that allow working  across different operating systems. 
14. Expose `_private` via `@property` **only when** outside code needs to read the value but must never change it, delete it, or supply an invalid one—everything else can stay hidden.
15. 


## reference code snippet
### object detection 
```

from ultralytics import YOLO

# Load a model
model = YOLO("yolo11n.pt")  # pretrained YOLO11n model

# Run batched inference on a list of images
results = model(["image1.jpg", "image2.jpg"], stream=True)  # return a generator of Results objects

# Process results generator
for result in results:
    boxes = result.boxes  # Boxes object for bounding box outputs
    result.show()  # display to screen
    result.save(filename="result.jpg")  # save to disk
```


instance segmentation 
```
from ultralytics import YOLO

# Load a model
model = YOLO("yolo11n-seg.pt")  # load an official model

# Predict with the model
results = model("https://ultralytics.com/images/bus.jpg")  # predict on an image

# Access the results
for result in results:
    xy = result.masks.xy  # mask in polygon format
    xyn = result.masks.xyn  # normalized
    masks = result.masks.data  # mask in matrix format (num_objects x H x W)
```

## supported image formats
bmp, dng, jpeg, mpo, png, tif, tiff, webp, HEIC
### supported video format
asf, mp4, mpeg, mov, mkv, avi, webm

### Results object attributes

1. orig_img
2. orig_shape
3. boxes
4. masks
5. path
6. names
7. speed
8. save_dir

### Return methods of Results object 
1. update() updates the Results object with new detection data (boxes, masks)
2. cpu() returns a copy of the Results object with all tensors moved to CPU memory.
3. numpy() returns a copy of Results object iwth all tensors converted to numpy arrays. 
4. to() returns a copy of Results object with tensors moved to specific device or datatype (dtype)
5. verbose() returns a long string for each tasks, detailing detection and classification outcomes. 
6. save_crop() saves cropped detection images to specified directory
7. to_json() converts detection results to JSON format which I want to implement in this project. 


### Masks class methods and properties
1. cpu()
2. numpy()
3. to()
4. xyn is a type Property (torch.Tensor) which is a list of normalized segments represented as tensors. 
5. xy is a type (Property(torch.Tensor)) which is also a list in pixel coordinates represented as tensors. 

### Box class methods and properties
1. cpu()
2. numpy()
3. to()
4. xyxy return the boxes in xyxy format
5. conf returns the confidence values of the boxes
6. cls returns the class values of the boxes
7. id return the track IDS of boxes if available
8. xywh returns the boxes in xywh format
9. xyxyn returns the boxes in xyxy format normalized by original image size. 

### Official code snippet to run inference on video using yolo model (from thread-safe inference guide )
```
import cv2

from ultralytics import YOLO

# Load the YOLO model
model = YOLO("yolo11n.pt")

# Open the video file
video_path = "path/to/your/video/file.mp4"
cap = cv2.VideoCapture(video_path)

# Loop through the video frames
while cap.isOpened():
    # Read a frame from the video
    success, frame = cap.read()

    if success:
        # Run YOLO inference on the frame
        results = model(frame)

        # Visualize the results on the frame
        annotated_frame = results[0].plot()

        # Display the annotated frame
        cv2.imshow("YOLO Inference", annotated_frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        # Break the loop if the end of the video is reached
        break

# Release the video capture object and close the display window
cap.release()
cv2.destroyAllWindows()
```


### suggested project structure for the application

This project structure is just a reference but for this project this can be tweaked according to the project requirements. 
```
oloy11/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── users.py
│   │   │   ├── posts.py
│   │   │   └── ...
│   │   └── v2/
│   │       └── ...
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── post.py
│   │   └── ...
│   ├── config.py
│   ├── database.py
│   └── utils.py
│
├── tests/
│   ├── __init__.py
│   ├── test_users.py
│   ├── test_posts.py
│   └── ...
│
├── .env
├── requirements.txt
├── Dockerfile
└── README.md

```

### FastAPI best practices
1. creating and registering custom middleware which allow efficienct logging, authentication and rate limiting. 
2. Enabling Cross-Origin Resource sharing which provide in-built support to control which domains can access your API, this is essential for modern web applicaqtions that rely on APIs on fetch and manipulate data. 
3. Use of FastAPI TestClient for writing testcases for fastapi app. 