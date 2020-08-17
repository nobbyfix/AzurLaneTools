# Azur Lane Asset Downloader and Extractor
This tool automatically downloads the newest assets directly from the game cdn servers and extracts the Texture2D files as png from them.

## HOW TO USE
### 1. Import files from obb/apk
While this is *not neccessary*, this step is **highly recommended**.    
The files from the obb/apk archives can easily be imported using the `obb_import.py` script:
```
./obb_import.py -f [FILEPATH]
```
The `FILEPATH` has to point to a valid obb/apk archive from one of the five game regions. The obb archive can be found on android in the folder `/storage/emulated/0/Android/obb/[APPCODE]/`.
The `APPCODE` differs depending on the region you want the obb archive from:
- EN: com.YoStarEN.AzurLane
- JP: com.YoStarJP.AzurLane
- KR: kr.txwy.and.blhx
- TW: com.hkmanjuu.azurlane.gp

Since the CN client is not distributed through the Google Play Store, there is no obb file for it. Therefore you need the apk which contains all the files. You can simply download the apk from one of the many app distributors or, if you already have the app installed, it can be found on android in the folder `/data/app/com.bilibili.azurlane-1/` (Note: you need root permission to access this folder).

### 2. Download new updates from the game
**Note: To prevent helping cheaters, two files needed for this part are missing. If you ask me nicely on Discord (nobbyfix#2338) i may provide them to you (usually only if you are an active wiki member).**

All assets that are usually distributed through the in-app downloader can be downloaded by simply executing:
```
./main.py -c [CLIENT]
```
where `CLIENT` has to be either EN, CN, JP, KR or TW. After all assets have been downloaded, you can find three files in the clients asset folder (at `ClientAssets/[CLIENT]/`):
- diff_new.txt
  - A list of all files that have been downloaded for the first time since the last update.
- diff_changed.txt
  - A list of all files that have been downloaded previously but have been changed since the last update.
- diff_deleted.txt
  - Mostly for curiosity, contains a list of all files that have been deleted since the last update.

### 3. Extract all new and changed files
**Note: This requires the additinal installation of two python libraries: UnityPy and unitypack** (yes it needs both, unitypack has shitty T2D support and UnityPy doesn't support Mesh export)

The newly downloaded assets can now be extracted by executing:
```
./extractor -c [CLIENT]
```
where `CLIENT` is again one of EN, CN, JP, KR or TW. The extracted images will then be saved in `ClientExtract/[CLIENT]/` Since only Texture2D assets are exported, its not desired to try to export from all assetbundles. Therefore in the config file `extract_config.json` is a list of all folders which should get extracted, which can be edited as desired.

Additionally all `painting`s will also be automatically reconstructed.

### 4. Enjoy the files

## Future plans and further notes
- planned: script that renames the files so they can be easily uploaded to the wiki
- planned: "compress" the images as desired for the wiki
- very far in the future: integration with the decompilation and json conversion routines
- **feel free to report issues or use the pull request feature**
