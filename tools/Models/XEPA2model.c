/*
XEPA (NV APEX) to OBJ/STL converter
Created by aspadm
*/

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>

#define XEPA_MAGIC 0x41504558
#define APEX_MAGIC 0x5D5C5B5A

#define FORMAT_APB_LETTER 98
#define FORMAT_APB 1
#define FORMAT_OBJ_LETTER 106
#define FORMAT_OBJ 2
#define FORMAT_STL_LETTER 108
#define FORMAT_STL 4
#define FORMAT_SHIFT -32

#define OK 0
#define INCORRECT_ARGS_COUNT 1
#define CANT_OPEN_INPUT_FILE 2
#define CANT_OPEN_OUTPUT_FILE 3
#define INCORRECT_APEX_FILE 4
#define UNKNOWN_FORMAT 5
#define CANT_ALLOC 6

#define DEBUG 0

typedef uint64_t UINT64;
typedef uint32_t DWORD;
typedef uint16_t SHORT;
typedef uint8_t BYTE;
typedef float U32;

void revert_bytes(DWORD * number);
int main(int argc, char ** argv);
int map_file(FILE *file, DWORD offset, DWORD *tris_count, DWORD *vert_off,
			 DWORD *norm_off, DWORD *uv_off, DWORD *ind_c, DWORD *ind_off);


int map_file(FILE *file, DWORD offset, DWORD *tris_count, DWORD *vert_off,
			 DWORD *norm_off, DWORD *uv_off, DWORD *ind_c, DWORD *ind_off)
{
	DWORD buf_dword;
	
	// search DATA_SECTION
	fseek(file, offset + 24, SEEK_SET);
	fread(&buf_dword, 4, 1, file);
	revert_bytes(&buf_dword);
	//printf("data_section %u\n", buf_dword);
	
	// search objectTable data offset
	fseek(file, offset + buf_dword, SEEK_SET);
	fread(&buf_dword, 4, 1, file);
	//printf("objectTable data offset %u\n", buf_dword);
	
	// search graphicalLods offset
	fseek(file, offset + buf_dword + 144, SEEK_SET);
	fread(&buf_dword, 4, 1, file);
	//printf("graphicalLods offset %u\n", buf_dword);
	
	// search real lods offset
	fseek(file, offset + buf_dword, SEEK_SET);
	fread(&buf_dword, 4, 1, file);
	//printf("real lods offset %u\n", buf_dword);
	
	// search renderMeshAsset
	fseek(file, offset + buf_dword + 152, SEEK_SET);
	fread(&buf_dword, 4, 1, file);
	//printf("renderMeshAsset offset %u\n", buf_dword);
	
	// search submesh offset
	fseek(file, offset + buf_dword + 120, SEEK_SET);
	fread(&buf_dword, 4, 1, file);
	//printf("submesh offset %u\n", buf_dword);
	
	// search real submesh offset
	fseek(file, offset + buf_dword, SEEK_SET);
	fread(&buf_dword, 4, 1, file);
	//printf("real submesh offset %u\n", buf_dword);
	
	// search index buffer offset
	fseek(file, offset + buf_dword + 128, SEEK_SET);
	fread(ind_off, 4, 1, file);
	*ind_off += offset;
	//printf("INDEX BUFFER OFFSET %u\n", *ind_off);
	
	// search index array size
	fseek(file, offset + buf_dword + 144, SEEK_SET);
	fread(ind_c, 4, 1, file);
	//printf("INDEX BUFFER SIZE %u\n", *ind_c);
	*ind_c = *ind_c / 3;
	
	// search vertexBuffer offset
	fseek(file, offset + buf_dword + 120, SEEK_SET);
	fread(&buf_dword, 4, 1, file);
	//printf("vertexBuffer %u\n", buf_dword);
	
	// search uv/points/normals size
	fseek(file, offset + buf_dword + 120, SEEK_SET);
	fread(tris_count, 4, 1, file);
	//printf("TRIS COUNT %u\n", *tris_count);
	
	// search vertexFormat offset
	fseek(file, offset + buf_dword + 128, SEEK_SET);
	fread(&buf_dword, 4, 1, file);
	//printf("vertexFormat %u\n", buf_dword);
	
	// search index buffer offset
	fseek(file, offset + buf_dword + 152, SEEK_SET);
	fread(vert_off, 4, 1, file);
	fseek(file, offset + *vert_off + 120, SEEK_SET);
	fread(vert_off, 4, 1, file);
	*vert_off += offset;
	//printf("VERTEX BUFFER OFFSET %u\n", *vert_off);
	
	// search normal buffer offset
	fseek(file, offset + buf_dword + 160, SEEK_SET);
	fread(norm_off, 4, 1, file);
	fseek(file, offset + *norm_off + 120, SEEK_SET);
	fread(norm_off, 4, 1, file);
	*norm_off += offset;
	//printf("NORMAL BUFFER OFFSET %u\n", *norm_off);
	
	// search UV buffer offset
	fseek(file, offset + buf_dword + 176, SEEK_SET);
	fread(uv_off, 4, 1, file);
	fseek(file, offset + *uv_off + 120, SEEK_SET);
	fread(uv_off, 4, 1, file);
	*uv_off += offset;
	//printf("UV BUFFER OFFSET %u\n", *uv_off);
	
	return OK;
}


void revert_bytes(DWORD * number)
{
	*number = ((*number & 0xFF) << 24) |
			((*number & 0xFF00) <<  8) |
		  ((*number & 0xFF0000) >>  8) |
		((*number & 0xFF000000) >> 24);
}

int main(int argc, char ** argv)
{
	setbuf(stdout, NULL);
    setbuf(stdin, NULL);
	
	DWORD apex_magic;
	DWORD apex_start_offset = 0;
	BYTE bufer;
	BYTE out_format;
	
	FILE *apex_file = NULL;
	FILE *out_file = NULL;
	
	if (argc != 3)
	{
		if (argc !=1)
		{
			printf("Incorrect args count\n");
		}
		else
		{
			printf("DEMD XEPA to APB/OBJ/STL converter v0.9 (17.09.2017) by aspadm\n");
		}
		
		printf("\nUsage: XEPA2model <input.apx> <output.[apb/stl/obj]>");
		
		return INCORRECT_ARGS_COUNT;
	}
	
	for (int i = 0; argv[2][i] != 0; i++)
	{
		out_format = argv[2][i];
	}
	
	switch (out_format)
	{
		case FORMAT_APB_LETTER:
		case FORMAT_APB_LETTER + FORMAT_SHIFT:
			out_format = FORMAT_APB;
			break;
		case FORMAT_OBJ_LETTER:
		case FORMAT_OBJ_LETTER + FORMAT_SHIFT:
			out_format = FORMAT_OBJ;
			break;
		case FORMAT_STL_LETTER:
		case FORMAT_STL_LETTER + FORMAT_SHIFT:
			out_format = FORMAT_STL;
			break;
		default:
			printf("Unknown format to save");
			return UNKNOWN_FORMAT;
			break;
	}
	
	apex_file = fopen(argv[1], "rb");
	if (apex_file == NULL)
	{
		printf("Can't open file: '%s'", argv[1]);
		
		return CANT_OPEN_INPUT_FILE;
	}
	setbuf(apex_file, NULL);
	
	if (fread(&apex_magic, 4, 1, apex_file) != 1)
	{
		printf("Can't read from file: '%s'", argv[1]);
		
		return CANT_OPEN_INPUT_FILE;
	}
	
	if (apex_magic == APEX_MAGIC)
	{
		if (out_format == FORMAT_APB)
		{
			printf("\nSource file is already converted APB file");
			
			return OK;
		}
	}
	else
	{
		if (apex_magic != XEPA_MAGIC)
		{
			printf("'%s' not a XEPA file:\ngot a signature 0x%x (correct is 0x%x)",
			argv[1], apex_magic, XEPA_MAGIC);
			
			return INCORRECT_APEX_FILE;
		}
		else
		{
			while (1)
			{
				if (fread(&apex_magic, 4, 1, apex_file) != 1)
				{
					printf("Can't find APEX magic in file: %s", argv[1]);
					
					return INCORRECT_APEX_FILE;
				}
				
				if (apex_magic == APEX_MAGIC)
				{
					break;
				}
				
				if (fseek(apex_file, -3, SEEK_CUR) != 0)
				{
					printf("Can't read from file: '%s'", argv[1]);
					
					return CANT_OPEN_INPUT_FILE;
				}
			}
		}			
	}	
	
	if (fseek(apex_file, -4, SEEK_CUR) != 0)
	{
		printf("Can't read from file: '%s'", argv[1]);
		
		return CANT_OPEN_INPUT_FILE;
	}
	apex_start_offset = ftell(apex_file);
		
	if (out_format == FORMAT_APB)
	{
		fseek(apex_file, 16, SEEK_CUR);
		DWORD content_lenght;
		if (fread(&content_lenght, 4, 1, apex_file) != 1)
		{
			printf("Can't read from file: '%s'", argv[1]);
			
			return CANT_OPEN_INPUT_FILE;
		}
		revert_bytes(&content_lenght);
		content_lenght += 4;
		fseek(apex_file, -20, SEEK_CUR);
		
		printf("Start APB export");
		
		out_file = fopen(argv[2], "wb");
		if (out_file == NULL)
		{
			printf("Can't create file: '%s'", argv[2]);
			
			return CANT_OPEN_OUTPUT_FILE;
		}
	
		for (int i = 0; i < content_lenght; i++)
		{
			if (fread(&bufer, 1, 1, apex_file) != 1)
			{
				printf("Can't read from file: '%s'", argv[1]);
			
				return CANT_OPEN_INPUT_FILE;
			}
			if (fwrite(&bufer, 1, 1, out_file) != 1)
			{
				printf("Can't write to file: '%s'", argv[2]);
			
				return CANT_OPEN_OUTPUT_FILE;
			}
		}
		
		fclose(apex_file);
		fclose(out_file);
		
		printf("\nExport is done");
	
		return OK;
	}
	
	DWORD triangles; // vertexes count
	DWORD vert;
	DWORD norm;
	DWORD uv;
	DWORD ind_c; // indexes count
	DWORD indexes;
	
	if (map_file(apex_file, apex_start_offset, &triangles, &vert, &norm, &uv, &ind_c, &indexes) != OK)
	{
		printf("Can't read from file: '%s'", argv[1]);
			
		return CANT_OPEN_INPUT_FILE;
	}
	
	// DEBUG
	//printf("\nOFFSET %u\n", apex_start_offset);
	//printf("\n\ntris %u vert %u norm %u uv %u ind_c %u ind %u\n\n", triangles, vert, norm, uv, ind_c, indexes);
	// DEBUG END
	
	U32 *vert_arr = (U32*) malloc(triangles*12);
	U32 *norm_arr = (U32*) malloc(triangles*12);
	DWORD *index_arr = (DWORD*) malloc(ind_c*12);
	
	if ((vert_arr == NULL) || (norm_arr == NULL) || (index_arr == NULL))
	{
		printf("Can't allocate memory. Clean RAM and start program again");
		
		return CANT_ALLOC;
	}
	
	if (fseek(apex_file, vert, SEEK_SET) != 0)
	{
		printf("Can't seek vert offset");
		
		return CANT_OPEN_INPUT_FILE;
	}
	if (fread(vert_arr, 4, triangles*3, apex_file) != triangles*3)
	{
		printf("Can't read vertices from file '%s'", argv[1]);
		
		return CANT_OPEN_INPUT_FILE;
	}
	
	if (fseek(apex_file, norm, SEEK_SET) != 0)
	{
		printf("Can't seek normals offset");
		
		return CANT_OPEN_INPUT_FILE;
	}
	if (fread(norm_arr, 4, triangles*3, apex_file) != triangles*3)
	{
		printf("Can't read normals from file '%s'", argv[1]);
		
		return CANT_OPEN_INPUT_FILE;
	}
	
	if (fseek(apex_file, indexes, SEEK_SET) != 0)
	{
		printf("Can't seek index offset");
		
		return CANT_OPEN_INPUT_FILE;
	}
	if (fread(index_arr, 4, ind_c*3, apex_file) != ind_c*3)
	{
		printf("Can't read %d indexes from file '%s'", ind_c, argv[1]);

		return CANT_OPEN_INPUT_FILE;
	}
	
	if (out_format == FORMAT_STL)
	{
		printf("Start STL export");
		
		out_file = fopen(argv[2], "wb");
		if (out_file == NULL)
		{
			printf("Can't create file: '%s'", argv[2]);
			
			return CANT_OPEN_OUTPUT_FILE;
		}
		
		bufer = 0;
		for (int i = 0; i < 80; i++)
		{
			if (fwrite(&bufer, 1, 1, out_file) != 1)
			{
				printf("Can't write to file: '%s'", argv[2]);
			
				return CANT_OPEN_OUTPUT_FILE;
			}
		}
		
		if (fwrite(&ind_c, 4, 1, out_file) != 1)
		{
			printf("Can't write to file: '%s'", argv[2]);
		
			return CANT_OPEN_OUTPUT_FILE;
		}	
		
		for (unsigned int i = 0; i < ind_c; i++)
		{
			for (int j = 0; j < 12; j++)
			{
				fwrite(&bufer, 1, 1, out_file);
			}
			
			fwrite(vert_arr+3*index_arr[i*3], 4, 3, out_file);
			fwrite(vert_arr+3*index_arr[i*3+1], 4, 3, out_file);
			fwrite(vert_arr+3*index_arr[i*3+2], 4, 3, out_file);
			fwrite(&bufer, 1, 1, out_file);
			fwrite(&bufer, 1, 1, out_file);
		}
		
		printf("\nExport is done");
	
		return OK;
	}
	
	U32 *uv_arr = (U32*) malloc(triangles*8);
	if (uv_arr == NULL)
	{
		printf("Can't allocate memory. Clean RAM and start program again");
		
		return CANT_ALLOC;
	}
	
	if (fseek(apex_file, uv, SEEK_SET) != 0)
	{
		printf("Can't seek UV offset");
		
		return CANT_OPEN_INPUT_FILE;
	}
	if (fread(uv_arr, 4, triangles*2, apex_file) != triangles*2)
	{
		printf("Can't read UV from file '%s'", argv[1]);
		
		return CANT_OPEN_INPUT_FILE;
	}
	
	if (out_format == FORMAT_OBJ)
	{
		printf("Start OBJ export");
		
		out_file = fopen(argv[2], "w");
		if (out_file == NULL)
		{
			printf("Can't create file: '%s'", argv[2]);
			
			return CANT_OPEN_OUTPUT_FILE;
		}
		
		fprintf(out_file, "# Created using XEPA (NV APEX) to OBJ/STL converter v0.9 by aspadm\n");
		fprintf(out_file, "# %d vertices/normals/UV's; %d triangles\n\n# Vertix array\n", triangles, ind_c);
		
		for (unsigned int i = 0; i < triangles; i++)
		{
			fprintf(out_file, "v %f %f %f\n", vert_arr[i*3],
					vert_arr[i*3 + 1], vert_arr[i*3 + 2]);
		}
		
		fprintf(out_file, "\n# Normal array\n");
		
		for (unsigned int i = 0; i < triangles; i++)
		{
			fprintf(out_file, "vn %f %f %f\n", norm_arr[i*3],
					norm_arr[i*3 + 1], norm_arr[i*3 + 2]);
		}
		
		fprintf(out_file, "\n# UV array\n");
		
		for (unsigned int i = 0; i < triangles; i++)
		{
			fprintf(out_file, "vt %f %f\n", uv_arr[i*2], uv_arr[i*2 + 1]);
		}
		
		fprintf(out_file, "\n# Polygonal array\n");
		
		for (unsigned int i = 0; i < ind_c; i++)
		{
			fprintf(out_file, "f %u/%u/%u %u/%u/%u %u/%u/%u\n", index_arr[i*3] + 1,
					index_arr[i*3] + 1, index_arr[i*3] + 1, index_arr[i*3 + 1] + 1, index_arr[i*3 + 1] + 1,
					index_arr[i*3 + 1] + 1, index_arr[i*3 + 2] + 1, index_arr[i*3 + 2] + 1, index_arr[i*3 + 2] + 1);
		}
		
		printf("\nExport is done");
	
		return OK;
	}
}