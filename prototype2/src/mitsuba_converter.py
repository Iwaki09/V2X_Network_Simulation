from .scene_parser import Scene

def shape_to_xml(shape_info, material_id):
    """Converts a single shape (building or vehicle) to a Mitsuba XML string."""
    shape_type = "cube"
    center = shape_info['position']
    size = shape_info['size']
    
    # Mitsuba's cube is centered at (0,0,0) by default and has a size of 2x2x2.
    # We need to use transformations to place and scale it correctly.
    # 1. Translate to the desired center position.
    # 2. Scale to match the desired size (size is diameter, so we use half-size for scaling).
    transform_xml = f"""
        <transform name="to_world">
            <translate x="{center[0]}" y="{center[1]}" z="{center[2] + size[2]/2}"/>
            <scale x="{size[0]/2}" y="{size[1]/2}" z="{size[2]/2}"/>
        </transform>
    """

    return f"""
    <shape type="{shape_type}" id="{shape_info['id']}" name="{shape_info['id']}">
        {transform_xml}
        <ref id="{material_id}"/>
    </shape>
    """

def material_to_xml(material_id, material_info):
    """Converts a single material to a Mitsuba XML string."""
    mat_type = material_info.get("type", "dielectric")
    if mat_type == "dielectric":
        return f"""
    <bsdf type="dielectric" id="{material_id}">
        <float name="int_ior" value="{material_info.get('int_ior', 1.5)}"/>
        <float name="ext_ior" value="{material_info.get('ext_ior', 1.0)}"/>
    </bsdf>
    """
    elif mat_type == "conductor":
        return f"""
    <bsdf type="conductor" id="{material_id}">
        <string name="material" value="{material_info.get('material', 'Au')}"/>
    </bsdf>
    """
    return ""

def scene_to_mitsuba_xml(scene: Scene) -> str:
    """
    Converts a Scene object into a Mitsuba 3 XML scene description.

    Args:
        scene: The Scene object loaded from JSON.

    Returns:
        A string containing the full XML scene description.
    """
    xml_parts = ['<scene version="3.0.0">']

    # Integrator (use surface integrator for ray tracing)
    xml_parts.append('<integrator type="direct"/>')

    # Materials with HolderMaterial for SIONNA RT
    xml_parts.append('''
    <bsdf type="holder-material" id="concrete">
        <bsdf type="itu" id="concrete_itu">
            <string name="itu_type" value="concrete"/>
            <float name="thickness" value="0.2"/>
        </bsdf>
    </bsdf>
    
    <bsdf type="holder-material" id="ground">
        <bsdf type="itu" id="ground_itu">
            <string name="itu_type" value="concrete"/>
            <float name="thickness" value="0.1"/>
        </bsdf>
    </bsdf>
    ''')

    # Shapes (Buildings only - focus on main geometry)
    for building in scene.buildings:
        pos = building['position']
        size = building['size']
        center_x = pos[0] + size[0] / 2
        center_y = pos[1] + size[1] / 2
        center_z = pos[2] + size[2] / 2
        
        xml_parts.append(f'''
    <shape type="cube" id="{building['id']}">
        <transform name="to_world">
            <translate x="{center_x}" y="{center_y}" z="{center_z}"/>
            <scale x="{size[0]/2}" y="{size[1]/2}" z="{size[2]/2}"/>
        </transform>
        <ref id="concrete"/>
    </shape>''')

    # Simple ground plane
    xml_parts.append(f'''
    <shape type="rectangle" id="ground_plane">
        <transform name="to_world">
            <translate x="{scene.world_size[0]/2}" y="{scene.world_size[1]/2}" z="0"/>
            <scale x="{scene.world_size[0]/2}" y="{scene.world_size[1]/2}" z="1"/>
        </transform>
        <ref id="ground"/>
    </shape>''')

    xml_parts.append('</scene>')

    return "\n".join(xml_parts)


