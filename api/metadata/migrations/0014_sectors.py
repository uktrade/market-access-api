import uuid
from django.db import migrations

sectors_mapping = [
    {
        'src': 'Clothing, Footwear and Fashion',
        'src_id': '9c38cecc-5f95-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Consumer and retail', 'id': '355f977b-8ac3-e211-a646-e4115bead28a'}
        ]
    },
    {
        'src': 'Communications',
        'src_id': '9d38cecc-5f95-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Technology and smart cities', 'id': 'ac959812-6095-e211-a939-e4115bead28a'}
        ]
    },
    {
        'src': 'Defence and Security',
        'src_id': 'b0959812-6095-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Defence', 'id': '7dbb9fc6-5f95-e211-a939-e4115bead28a'},
            {'name': 'Security', 'id': 'a438cecc-5f95-e211-a939-e4115bead28a'}
        ]
    },
    {
        'src': 'Electronics and IT Hardware',
        'src_id': 'a138cecc-5f95-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Technology and smart cities', 'id': 'ac959812-6095-e211-a939-e4115bead28a'}
        ]
    },
    {
        'src': 'Environment and Water',
        'src_id': 'b2959812-6095-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Environment', 'id': 'a238cecc-5f95-e211-a939-e4115bead28a'},
            {'name': 'Water', 'id': 'ae22c9d2-5f95-e211-a939-e4115bead28a'}
        ]
    },
    {
        'src': 'Giftware, Jewellery and Tableware',
        'src_id': 'a638cecc-5f95-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Consumer and retail', 'id': '355f977b-8ac3-e211-a646-e4115bead28a'}
        ]
    },
    {
        'src': 'Healthcare and Medical',
        'src_id': 'a738cecc-5f95-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Healthcare services', 'id': 'a738cecc-5f95-e211-a939-e4115bead28a'},
            {'name': 'Medical devices and equipment', 'id': '6f535406-6095-e211-a939-e4115bead28a'}
        ]
    },
    {
        'src': 'Household Goods, Furniture and Furnishings',
        'src_id': 'a838cecc-5f95-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Consumer and retail', 'id': '355f977b-8ac3-e211-a646-e4115bead28a'}
        ]
    },
    {
        'src': 'ICT',
        'src_id': 'b3959812-6095-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Technology and smart cities', 'id': 'ac959812-6095-e211-a939-e4115bead28a'}
        ]
    },
    {
        'src': 'Leisure and Tourism',
        'src_id': 'a938cecc-5f95-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Consumer and retail', 'id': '355f977b-8ac3-e211-a646-e4115bead28a'}
        ]
    },
    {
        'src': 'Life Sciences',
        'src_id': 'b4959812-6095-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Pharmaceuticals and biotechnology', 'id': '9938cecc-5f95-e211-a939-e4115bead28a'}
        ]
    },
    {
        'src': 'Mass Transport',
        'src_id': 'b5959812-6095-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Airports', 'id': '9738cecc-5f95-e211-a939-e4115bead28a'},
            {'name': 'Railways', 'id': 'aa22c9d2-5f95-e211-a939-e4115bead28a'},
            {'name': 'Maritime', 'id': 'aa38cecc-5f95-e211-a939-e4115bead28a'}
        ]
    },
    {
        'src': 'Mechanical Electrical and Process Engineering',
        'src_id': 'ab38cecc-5f95-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Advanced engineering', 'id': 'af959812-6095-e211-a939-e4115bead28a'}
        ]
    },
    {
        'src': 'Metallurgical Process Plant',
        'src_id': 'a422c9d2-5f95-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Advanced engineering', 'id': 'af959812-6095-e211-a939-e4115bead28a'}
        ]
    },
    {
        'src': 'Metals, Minerals and Materials',
        'src_id': 'a522c9d2-5f95-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Advanced engineering', 'id': 'af959812-6095-e211-a939-e4115bead28a'}
        ]
    },
    {
        'src': 'Oil and Gas',
        'src_id': 'a722c9d2-5f95-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Energy', 'id': 'b1959812-6095-e211-a939-e4115bead28a'}
        ]
    },
    {
        'src': 'Ports and Logistics',
        'src_id': 'a822c9d2-5f95-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Maritime', 'id': 'aa38cecc-5f95-e211-a939-e4115bead28a'}
        ]
    },
    {
        'src': 'Power',
        'src_id': 'a922c9d2-5f95-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Energy', 'id': 'b1959812-6095-e211-a939-e4115bead28a'}
        ]
    },
    {
        'src': 'Renewable Energy',
        'src_id': '7ebb9fc6-5f95-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Energy', 'id': 'b1959812-6095-e211-a939-e4115bead28a'}
        ]
    },
    {
        'src': 'Software and Computer Services Business to Business (B2B)',
        'src_id': 'ab22c9d2-5f95-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Technology and smart cities', 'id': 'ac959812-6095-e211-a939-e4115bead28a'}
        ]
    },
    {
        'src': 'Textiles, Interior Textiles and Carpets',
        'src_id': 'ad22c9d2-5f95-e211-a939-e4115bead28a',
        'dest': [
            {'name': 'Consumer and retail', 'id': '355f977b-8ac3-e211-a646-e4115bead28a'}
        ]
    },
]


def migrate_sectors(apps, schema_editor):
    BarrierInstance = apps.get_model("barriers", "BarrierInstance")
    HistoricalBarrierInstance = apps.get_model("barriers", "HistoricalBarrierInstance")

    barriers = BarrierInstance.objects.all()
    historical_barriers = HistoricalBarrierInstance.objects.all()

    for map in sectors_mapping:
        src_sector_id = uuid.UUID(map["src_id"])
        dest_sector_ids = [sector["id"] for sector in map["dest"]]

        # Update barriers
        for barrier in barriers.filter(sectors__contains=[src_sector_id]):
            barrier.sectors.remove(src_sector_id)
            barrier.sectors.extend(dest_sector_ids)
            barrier.save()

        # Update historic barriers
        for historical_barrier in historical_barriers.filter(sectors__contains=[src_sector_id]):
            historical_barrier.sectors.remove(src_sector_id)
            historical_barrier.sectors.extend(dest_sector_ids)
            historical_barrier.save()


class Migration(migrations.Migration):
    """
    Migrating sectors to match the new dataset provided in metadata.
    """
    dependencies = [
        ('metadata', '0013_barriertag'),
    ]

    operations = [
        migrations.RunPython(migrate_sectors, reverse_code=migrations.RunPython.noop),
    ]
