import subprocess, json, numpy, math
from types import new_class
from sklearn.cluster import KMeans
import cv2 as cv 
import style

def get_screensize():
    """
    Definition:
    -----------
    Function returns the screen resolution of the display connected to the raspberry pi HDMI port.\n
    command only works when run via the said monitor...will definitely give an error when run via SSH on a laptop\n

    Returns:
    --------
    (`read_status` [bool], `width` [int], `height` [int]) : tuple 
    \n
    read_status : True means screen size read successfully...False means otherwise\n
    width       : width of screen in pixels\n
    height      : height of screen in pixels\n
    \n
    """
    
    try:
        # [NOTE EXPLANATION] Run subprocess module with command to get screen resolution.
        output = subprocess.Popen('xrandr | grep "\*" | cut -d" " -f4',shell=True, stdout=subprocess.PIPE).communicate()[0]
        resolution = output.split()[0].split(b'x')
        return True, int(resolution[0]), int(resolution[1])
    except Exception as err:
        # print('Error occured while getting screen size with message: {}'.format(err))
        return False, 0, 0

def get_mean_colors(pngfile, jsonfile, outputpath):
    """
    Definition:
    -----------
    Function isolates a section of a '.png' file based on its coordinates and determines the dominant color of said section.\n
    A region of interest is defined (via coordinates provided in json) in an image.\n
    Based on the coordinates the image is cropped and the region is isolated.\n
    The dominant color is selected via K-cluster algorithm and the rgb values of individual ROI are appended to the json file.\n
    \n
    
    Attributes:
    -----------
    `pngfile` : String
        filepath and filename of image whos mean color is to be determined.\n

    `jsonfile` : String
        filepath and filename of json file containing the coordinates of the ROI.\n

    `outputpath` : String
        filepath where the photos created during cropping are to be stored
    
    """
    # [NOTE EXPLANATION] Read png-image and json-file.
    image = cv.imread(pngfile, cv.IMREAD_UNCHANGED)

    with open(jsonfile, 'r') as file:
        config = json.load(file)
        file.close()
    
    for key in config:
        coordinate_list = numpy.array(config[key]['coordinates'])

        # [NOTE EXPLANATION] Find out image extreme coordinates of image.
        extremes = cv.boundingRect(coordinate_list)
        x, y, w, h = extremes
        extremes_list = [x, y, w, h]
        # print('extremes', extremes)
        cropped_img = image[y: y+h, x: x+w].copy()

        coordinate_list = coordinate_list - coordinate_list.min(axis=0)

        # [NOTE EXPLANATION] Create an image mask based on the ROI coordinates.
        mask = numpy.zeros(cropped_img.shape[:2], numpy.uint8)
        cv.drawContours(mask, [coordinate_list], -1, (255, 255, 255), -1, cv.LINE_AA)

        # [NOTE EXPLANATION] Create an image with ROI isolated via black-background.
        blackbg_img = cv.bitwise_and(cropped_img, cropped_img, mask=mask)

        # [NOTE EXPLANATION] Create an image with ROI isolated via white-background.
        bg = numpy.ones_like(cropped_img, numpy.uint8)*255
        cv.bitwise_not(bg, bg, mask=mask)
        whitebg_img = bg + blackbg_img

        # [NOTE EXPLANATION] Create an image with ROI isolated via no-background.
        temp = cv.cvtColor(blackbg_img, cv.COLOR_BGR2GRAY)
        _, alpha = cv.threshold(temp, 0, 255, cv.THRESH_BINARY)
        b, g, r = cv.split(blackbg_img)
        rgba = [b, g, r, alpha]
        isolated_img = cv.merge(rgba, 4)

        # [NOTE EXPLANATION] Calculate mean/average color of isolated image.
        # mean_color = ((numpy.array(cv.mean(isolated_img)).astype(numpy.uint8)).tolist())
        # config[key]['mean_color'] = mean_color
        # print('mean color is {}'.format(mean_color))

        # [NOTE EXPLANATION] Calculate dominant color of isolated image using K-means clustering.
        rgb_image = cv.cvtColor(isolated_img, cv.COLOR_BGR2RGB)
        rgb_image = rgb_image.reshape((rgb_image.shape[0] * rgb_image.shape[1], 3))
        cluster = KMeans(n_clusters=style.K_CLUSTER_SIZE).fit(rgb_image)
        labels = numpy.arange(0, len(numpy.unique(cluster.labels_)) + 1)
        (hist, _) = numpy.histogram(cluster.labels_, bins = labels)
        hist = hist.astype('float')
        hist /= hist.sum()
        colors = sorted([(percent, color) for (percent, color) in zip(hist, cluster.cluster_centers_)])
        dom_rgb = max(colors, key=lambda item:item[0])[1]
        dom_rgb = [int(dom_rgb[2]), int(dom_rgb[1]), int(dom_rgb[0])]
        # print('dominant color is', dom_rgb)
        config[key]['mean_color'] = dom_rgb
        config[key]['extremes_of_ROI'] = extremes_list

        # [NOTE EXPLANATION] Store images if required.        
        if style.CREATE_FILES == True: 
            cv.imwrite(outputpath + str(key) + style.CROPPED_IMAGE   , cropped_img)
            cv.imwrite(outputpath + str(key) + style.MASK_ONLY       , mask)
            cv.imwrite(outputpath + str(key) + style.BLACK_BACKGROUND, blackbg_img)
            cv.imwrite(outputpath + str(key) + style.WHITE_BACKGROUND, whitebg_img)
            cv.imwrite(outputpath + str(key) + style.ISOLATED_ROI    , isolated_img)

    # [NOTE EXPLANATION] Write data to json file.
    with open(jsonfile, 'w') as file:
        file.write(json.dumps(config))
        file.close()


def compare_colors(filename, reference_jsonfile, output_jsonfile, outputpath):
    """
    Definition:
    -----------
    Function isolates a section of a '.png' file based on its coordinates and compares the dominant color with a reference color.\n
    A region of interest is defined (via coordinates provided in json) in an image.\n
    Based on the coordinates the image is cropped and the region is isolated.\n
    The dominant color is selected via K-cluster algorithm and the rgb values are compared with the reference rgb values provided in the json file.\n
    This output is stored in another json file\n
    
    Attributes:
    -----------
    `pngfile` : String
        filepath and filename of image whos mean color is to be determined.\n

    `jsonfile` : String
        filepath and filename of json file containing the coordinates of the ROI.\n

    `output_jsonfile` : String
        filepath and filename of json file containing the results of image-processing.\n

    `outputpath` : String
        filepath where the photos created during cropping are to be stored
    
    """
    # [NOTE EXPLANATION] Read png-image and json-file.
    output_config = {}
    image = cv.imread(filename, cv.IMREAD_UNCHANGED)

    with open(reference_jsonfile, 'r') as file:
        input_config = json.load(file)
        file.close()

    for key in input_config:
        output_config[key] = {}
        coordinate_list = numpy.array(input_config[key]['coordinates'])

        # [NOTE EXPLANATION] Find out image extreme coordinates of image.
        extremes = cv.boundingRect(coordinate_list)
        x, y, w, h = extremes
        cropped_img = image[y: y+h, x: x+w].copy()

        coordinate_list = coordinate_list - coordinate_list.min(axis=0)

        # [NOTE EXPLANATION] Create an image mask based on the ROI coordinates.
        mask = numpy.zeros(cropped_img.shape[:2], numpy.uint8)
        cv.drawContours(mask, [coordinate_list], -1, (255, 255, 255), -1, cv.LINE_AA)

        # [NOTE EXPLANATION] Create an image with ROI isolated via black-background.
        blackbg_img = cv.bitwise_and(cropped_img, cropped_img, mask=mask)

        # [NOTE EXPLANATION] Create an image with ROI isolated via white-background.
        bg = numpy.ones_like(cropped_img, numpy.uint8)*255
        cv.bitwise_not(bg, bg, mask=mask)
        whitebg_img = bg + blackbg_img

        # [NOTE EXPLANATION] Create an image with ROI isolated via no-background.
        temp = cv.cvtColor(blackbg_img, cv.COLOR_BGR2GRAY)
        _, alpha = cv.threshold(temp, 0, 255, cv.THRESH_BINARY)
        b, g, r = cv.split(blackbg_img)
        rgba = [b, g, r, alpha]
        isolated_img = cv.merge(rgba, 4)

        # [NOTE EXPLANATION] Calculate dominant color of isolated image using K-means clustering.
        rgb_image = cv.cvtColor(isolated_img, cv.COLOR_BGR2RGB)
        rgb_image = rgb_image.reshape((rgb_image.shape[0] * rgb_image.shape[1], 3))
        cluster = KMeans(n_clusters=style.K_CLUSTER_SIZE).fit(rgb_image)
        labels = numpy.arange(0, len(numpy.unique(cluster.labels_)) + 1)
        (hist, _) = numpy.histogram(cluster.labels_, bins = labels)
        hist = hist.astype('float')
        hist /= hist.sum()
        colors = sorted([(percent, color) for (percent, color) in zip(hist, cluster.cluster_centers_)])
        dom_rgb = max(colors, key=lambda item:item[0])[1]
        dom_rgb = [int(dom_rgb[2]), int(dom_rgb[1]), int(dom_rgb[0])]
        # print('dominant color is', dom_rgb)
        output_config[key]['mean_color'] = dom_rgb

        # mean_color = ((numpy.array(cv.mean(isolated_img)).astype(numpy.uint8)).tolist())
        # output_config[key]['mean_color'] = mean_color

        # [NOTE EXPLANATION] Store images if required. 
        if style.CREATE_FILES == True: 
            cv.imwrite(outputpath + str(key) + '_output' + style.CROPPED_IMAGE   , cropped_img)
            cv.imwrite(outputpath + str(key) + '_output' + style.MASK_ONLY       , mask)
            cv.imwrite(outputpath + str(key) + '_output' + style.BLACK_BACKGROUND, blackbg_img)
            cv.imwrite(outputpath + str(key) + '_output' + style.WHITE_BACKGROUND, whitebg_img)
            cv.imwrite(outputpath + str(key) + '_output' + style.ISOLATED_ROI, isolated_img)

        rgb_arr_1 =  input_config[key]['mean_color'][0:3]
        rgb_arr_2 = dom_rgb[0:3]

        # [NOTE EXPLANATION] Write data to json file.
        with open(style.APP_CONFIG_JSON, 'r') as file:
            param_config = json.load(file)
            file.close()

        # [NOTE EXPLANATION] Calculate desired error margin.
        if param_config["error_margin"] < 0     : error_margin = 0.0
        elif param_config["error_margin"] > 100 : error_margin = 100.0
        else: error_margin = float(param_config["error_margin"])
        
        # [NOTE EXPLANATION] compute eucledian distance between 2 colors.
        eucledian_distance = 0
        for color_component_1, color_component_2 in zip(rgb_arr_1, rgb_arr_2):
            eucledian_distance = eucledian_distance + (color_component_1 - color_component_2)**2

        eucledian_distance = round(((math.sqrt(eucledian_distance))*100/(255*1.732)), 2)
        output_config[key]['error'] = eucledian_distance

        # [NOTE EXPLANATION] Compare eucledian distance and error margin.
        if eucledian_distance < error_margin: 
            output_config[key]['success_status'] = True
            # print(eucledian_distance, error_margin, True)

        else: 
            output_config[key]['success_status'] = False
            # print(eucledian_distance, error_margin, False)

    # [NOTE EXPLANATION] Write data to json file.
    with open(output_jsonfile, 'w') as file:
        file.write(json.dumps(output_config))
        file.close()

def tkinter_compatible_color(arr):
    """
    Definition:
    -----------
    Function converts BGR values stored in an array to hexadecimal RGB values.\n
    Opencv interprets color in BGR format wheras Tkinter interprets it in RGB.\n
    
    Attributes:
    -----------
    `arr` : Int array
        B-G-R values of a color
    
    Returns:
    --------
    `color` : String
        hexadecimal representation of R-G-B values
    """
    color = '#'

    color_B = hex(arr[0])
    color_B = (color_B.replace('0x','')).replace('0X','')
    if len(color_B) == 1: color_B = '0' + color_B

    color_G = hex(arr[1])
    color_G = (color_G.replace('0x','')).replace('0X','')
    if len(color_G) == 1: color_G = '0' + color_G

    color_R = hex(arr[2])
    color_R = (color_R.replace('0x','')).replace('0X','')
    if len(color_R) == 1: color_R = '0' + color_R

    color = color + color_R + color_G + color_B
    return color
