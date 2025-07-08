<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology" version="3.42.1-Münster">
  <pipe-data-defined-properties>
    <Option type="Map">
      <Option name="name" type="QString" value=""/>
      <Option name="properties"/>
      <Option name="type" type="QString" value="collection"/>
    </Option>
  </pipe-data-defined-properties>
  <pipe>
    <provider>
      <resampling zoomedInResamplingMethod="nearestNeighbour" maxOversampling="2" zoomedOutResamplingMethod="nearestNeighbour" enabled="false"/>
    </provider>
    <rasterrenderer nodataColor="" alphaBand="-1" band="1" type="paletted" opacity="1">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <colorPalette>
        <paletteEntry color="#c3c3c3" label="Roads" value="1" alpha="255"/>
        <paletteEntry color="#828282" label="Buildings" value="2" alpha="255"/>
        <paletteEntry color="#409850" label="Evergreen trees" value="3" alpha="255"/>
        <paletteEntry color="#29bd0f" label="Deciduous trees" value="4" alpha="255"/>
        <paletteEntry color="#06e35d" label="Grass" value="5" alpha="255"/>
        <paletteEntry color="#dca20f" label="Bare soil" value="6" alpha="255"/>
        <paletteEntry color="#3b81d6" label="Water" value="7" alpha="255"/>
        <paletteEntry color="#06e35d" label="Grass wet (TARGET)" value="8" alpha="255"/>
        <paletteEntry color="#dcdcdc" label="Concrete (TARGET)" value="9" alpha="255"/>
      </colorPalette>
      <colorramp name="[source]" type="randomcolors">
        <Option/>
      </colorramp>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0" gamma="1"/>
    <huesaturation invertColors="0" colorizeRed="255" colorizeOn="0" colorizeBlue="128" grayscaleMode="0" colorizeStrength="100" saturation="0" colorizeGreen="128"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
