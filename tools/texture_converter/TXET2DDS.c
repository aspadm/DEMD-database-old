/*
TXET (DEMD textures) to DDS converter
Created by aspadm
*/

#include <stdio.h>
#include <stdint.h>

#define DDS_MAGIC 0x20534444
#define TXET_MAGIC 0x54455854

#define OK 0
#define INCORRECT_ARGS_COUNT 1
#define CANT_OPEN_INPUT_FILE 2
#define CANT_OPEN_OUTPUT_FILE 3
#define INCORRECT_TXET_FILE 4
#define UNKNOWN_FORMAT 5

#define FORMAT_01 0x5b
#define FORMAT_02 0x4a
#define FORMAT_03 0x58
#define FORMAT_04 0x53
#define FORMAT_05 0x50
#define FORMAT_06 0x56
#define FORMAT_07 0x0a
#define FORMAT_08 0x1c
#define FORMAT_09 0x23
#define FORMAT_10 0x43
#define FORMAT_11 0x3c

#define DEBUG 0

/*
 1: 5b: BC7_UNORM
 2: 4a: DXT1 / BC1
 3: 58: BC6H_UF16
 4: 53: BC4_UNORM
 5: 50: DXT5 / BC3
 6: 56: BC5_UNORM
 7: 0a: cubemap ?
 8: 1c: R8G8B8A8_UNORM
 9: 23: D32_FLOAT ?
10: 43: BC5_UNORM ?
11: 3c: R16_UNORM or B5G6R5_UNORM
*/

typedef uint32_t DWORD;
typedef uint16_t SHORT;
typedef uint8_t BYTE;

typedef struct {
	DWORD magic;
	DWORD dummy0;
	DWORD dummy1;
	DWORD content_lenght;
	DWORD dummy2;
	DWORD dummy3;
} TXET_HEADER;

typedef struct {
	SHORT dummy0[6];
	SHORT width;
	SHORT height;
	SHORT dummy1;
	SHORT format;
	SHORT dummy2[8];
} CONTENT_HEADER;

typedef struct {
	DWORD dwSize;
	DWORD dwFlags;
	DWORD dwFourCC;
	DWORD dwRGBBitCount;
	DWORD dwRBitMask;
	DWORD dwGBitMask;
	DWORD dwBBitMask;
	DWORD dwABitMask;
} DDS_PIXELFORMAT;

typedef struct {
	DWORD dwMagic;
	DWORD dwSize;
	DWORD dwFlags;
	DWORD dwHeight;
	DWORD dwWidth;
	DWORD dwPitchOrLinearSize;
	DWORD dwDepth;
	DWORD dwMipMapCount;
	DWORD dwReserved[11];
	DDS_PIXELFORMAT ddspf;
	DWORD dwCaps;
	DWORD dwCaps2;
	DWORD dwCaps3;
	DWORD dwCaps4;
	DWORD dwReserved2;
} DDS_HEADER;

typedef struct {
	DWORD dxgiFormat;
	DWORD resourceDimension;
	DWORD miscFlag;
	DWORD arraySize;
	DWORD miscFlags2;
} DDS_HEADER_DXT10;

int main(int argc, char ** argv);

int main(int argc, char ** argv)
{
	setbuf(stdout, NULL);
    setbuf(stdin, NULL);
	
	TXET_HEADER txet_header;
	CONTENT_HEADER txet_content;
	DDS_HEADER dds_header = {.dwMagic = DDS_MAGIC, .dwSize = 124, .dwMipMapCount = 1};
	DDS_HEADER_DXT10 dds_header_dxt10 = {0, 0, 0, 0, 0};
	BYTE bufer;
	FILE *tex_file = NULL;
	FILE *dds_file = NULL;
	
	if (argc != 3)
	{
		if (argc !=1)
		{
			printf("Incorrect args count\n");
		}
		else
		{
			printf("DEMD TXET to DDS converter v0.1 (30.08.2017) by aspadm\n");
		}
		
		printf("\nUsage: TXET2DDS <input.tex> <output.dds>");
		
		return INCORRECT_ARGS_COUNT;
	}

	tex_file = fopen(argv[1], "rb");
	if (tex_file == NULL)
	{
		printf("Can't open file: '%s'", argv[1]);
		
		return CANT_OPEN_INPUT_FILE;
	}
	
	if (fread(&txet_header, 24, 1, tex_file) != 1)
	{
		printf("Can't read from file: '%s'", argv[1]);
		
		return CANT_OPEN_INPUT_FILE;
	}
	
	if (txet_header.magic != TXET_MAGIC)
	{
		printf("'%s' not a TXET file:\ngot a signature 0x%x (correct is 0x%x)",
		argv[1], txet_header.magic, TXET_MAGIC);
		
		return INCORRECT_TXET_FILE;
	}
	
	if (DEBUG)
	{
		printf("TXET header:\n");
		printf("Header magic:\t%x\n", txet_header.magic);
		printf("Content bytes:\t%u\n", txet_header.content_lenght);
	}
	txet_header.content_lenght -= 36;
	
	if (fread(&txet_content, 36, 1, tex_file) != 1)
	{
		printf("Can't read from file: '%s'", argv[1]);
		
		return CANT_OPEN_INPUT_FILE;
	}
	
	if (DEBUG)
	{
		printf("\nContent header:\n");
		printf("Subformat:\t0x%x\n", txet_content.format);
		printf("Image width:\t%d\n", txet_content.width);
		printf("Image height:\t%d\n", txet_content.height);
	}
	
	if (DEBUG)
	{
		printf("\nCalculations:\n");
		printf("%u / (%u * %u) = %f bytes or %f bits\n",
		txet_header.content_lenght,
		txet_content.width,
		txet_content.height,
		(double)txet_header.content_lenght / (txet_content.width * txet_content.height),
		(double)txet_header.content_lenght * 8 / (txet_content.width * txet_content.height));
	}
	
	dds_file = fopen(argv[2], "wb");
	if (dds_file == NULL)
	{
		printf("Can't create file: '%s'", argv[2]);
		
		return CANT_OPEN_OUTPUT_FILE;
	}
	
	dds_header.dwHeight = txet_content.height;
	dds_header.dwWidth = txet_content.width;
	
	switch (txet_content.format)
	{
		case FORMAT_01:
			printf("Format 01: BC7_UNORM");
			//dds_header.dwFlags = 1052689;
			//dds_header.ddspf.dwFlags = 659463;
			//dds_header.dwPitchOrLinearSize = 4194304;
			
			dds_header.ddspf.dwSize = 32; // 4bpp
			dds_header.ddspf.dwFlags = 4; // dwFourCC enable
			dds_header.ddspf.dwFourCC = 808540228; // DX10
			
			dds_header_dxt10.dxgiFormat = 98; // BC7_UNORM
			dds_header_dxt10.resourceDimension = 3; // 2d texture
			dds_header_dxt10.arraySize = 1; // 1 texture
			break;
			
		case FORMAT_02:
			printf("Format 02: DXT1");
			//dds_header.dwPitchOrLinearSize = max(1, ((dds_header.dwWidth+3)/4)) * 8;
			//dds_header.dwFlags = 1052689;
			
			dds_header.ddspf.dwSize = 32; // 4bpp
			dds_header.ddspf.dwFlags = 4; // dwFourCC enable
			dds_header.ddspf.dwFourCC = 827611204; // DXT1
			break;
			
		case FORMAT_03:
			printf("Format 03: BC6H_UF16");
			
			dds_header.ddspf.dwSize = 32; // 4bpp
			dds_header.ddspf.dwFlags = 4; // dwFourCC enable
			dds_header.ddspf.dwFourCC = 808540228; // DX10
			
			dds_header_dxt10.dxgiFormat = 95; // BC6H_UF16
			dds_header_dxt10.resourceDimension = 3; // 2d texture
			dds_header_dxt10.arraySize = 1; // 1 texture
			break;
			
		case FORMAT_04:
			printf("Format 04: BC4_UNORM");
			
			dds_header.ddspf.dwSize = 32; // 4bpp
			dds_header.ddspf.dwFlags = 4; // dwFourCC enable
			dds_header.ddspf.dwFourCC = 808540228; // DX10
			
			dds_header_dxt10.dxgiFormat = 80; // BC4_UNORM
			dds_header_dxt10.resourceDimension = 3; // 2d texture
			dds_header_dxt10.arraySize = 1; // 1 texture
			break;
			
		case FORMAT_05:
			printf("Format 05: DXT5");
			//dds_header.dwFlags = 1052689;
			//dds_header.dwPitchOrLinearSize = max(1, ((dds_header.dwWidth+3)/4)) * 8;
			
			dds_header.ddspf.dwSize = 32; // 4bpp
			dds_header.ddspf.dwFlags = 4; // dwFourCC enable
			dds_header.ddspf.dwFourCC = 894720068; // DXT5
			break;

		case FORMAT_06:
			printf("Format 06: BC5_UNORM");
			
			dds_header.ddspf.dwSize = 32; // 4bpp
			dds_header.ddspf.dwFlags = 4; // dwFourCC enable
			dds_header.ddspf.dwFourCC = 808540228; // DX10
			
			dds_header_dxt10.dxgiFormat = 83; // BC5_UNORM
			dds_header_dxt10.resourceDimension = 3; // 2d texture
			dds_header_dxt10.arraySize = 1; // 1 texture
			break;
			
		case FORMAT_07:
			printf("Format 07: ?");
			
			dds_header.ddspf.dwSize = 32; // 4bpp
			dds_header.ddspf.dwFlags = 4; // dwFourCC enable
			dds_header.ddspf.dwFourCC = 808540228; // DX10
			
			dds_header_dxt10.dxgiFormat = 83; // BC5_UNORM
			dds_header_dxt10.resourceDimension = 3; // 2d texture
			dds_header_dxt10.arraySize = 1; // 1 texture
			break;
			
		case FORMAT_08:
			printf("Format 08: 32bpp");
			
			dds_header.ddspf.dwSize = 32; // 4bpp
			dds_header.ddspf.dwFlags = 4; // dwFourCC enable
			dds_header.ddspf.dwFourCC = 808540228; // DX10
			
			dds_header_dxt10.dxgiFormat = 28; // R8G8B8A8_UNORM
			dds_header_dxt10.resourceDimension = 3; // 2d texture
			dds_header_dxt10.arraySize = 1; // 1 texture
			break;
			
		case FORMAT_09:
			printf("Format 09: D32_FLOAT ?");
			
			dds_header.ddspf.dwSize = 32; // 4bpp
			dds_header.ddspf.dwFlags = 4; // dwFourCC enable
			dds_header.ddspf.dwFourCC = 808540228; // DX10
			
			dds_header_dxt10.dxgiFormat = 40; // D32_FLOAT
			dds_header_dxt10.resourceDimension = 3; // 2d texture
			dds_header_dxt10.arraySize = 1; // 1 texture
			break;
			
		case FORMAT_10:
			printf("Format 10: BC5_UNORM ?");
			
			dds_header.ddspf.dwSize = 32; // 4bpp
			dds_header.ddspf.dwFlags = 4; // dwFourCC enable
			dds_header.ddspf.dwFourCC = 808540228; // DX10
			
			dds_header_dxt10.dxgiFormat = 84; // BC5_UNORM
			dds_header_dxt10.resourceDimension = 3; // 2d texture
			dds_header_dxt10.arraySize = 1; // 1 texture
			break;
			
		case FORMAT_11:
			printf("Format 11: R16_UNORM ?");
			dds_header.ddspf.dwSize = 32; // 4bpp
			dds_header.ddspf.dwFlags = 4; // dwFourCC enable
			dds_header.ddspf.dwFourCC = 808540228; // DX10
			
			dds_header_dxt10.dxgiFormat = 56; // R16_UNORM
			//dds_header_dxt10.dxgiFormat = 85; // B5G6R5_UNORM
			dds_header_dxt10.resourceDimension = 3; // 2d texture
			dds_header_dxt10.arraySize = 1; // 1 texture
			break;
			
		default:
			printf("Unknown format");
			return UNKNOWN_FORMAT;
			break;
	}
	
	if (fwrite(&dds_header, 128, 1, dds_file) != 1)
	{
		printf("Can't write to file: '%s'", argv[2]);
		
		return CANT_OPEN_OUTPUT_FILE;
	}
	
	if (dds_header.ddspf.dwFourCC == 808540228)
	{
		if (fwrite(&dds_header_dxt10, 20, 1, dds_file) != 1)
		{
			printf("Can't write to file: '%s'", argv[2]);
		
			return CANT_OPEN_OUTPUT_FILE;
		}
	}
	
	for (int i = 0; i < txet_header.content_lenght; i++)
	{
		if (fread(&bufer, 1, 1, tex_file) != 1)
		{
			printf("Can't read from file: '%s'", argv[1]);
		
			return CANT_OPEN_INPUT_FILE;
		}
		if (fwrite(&bufer, 1, 1, dds_file) != 1)
		{
			printf("Can't write to file: '%s'", argv[2]);
		
			return CANT_OPEN_OUTPUT_FILE;
		}
	}
	
	printf("\nExport is done");
	
	return OK;
}