import pandas as pd
import os
import click
import platform

# Get the users Home Directory
if platform.system() == "Windows":
    from pathlib import Path
    homedir = str(Path.home())
else:
    homedir = os.environ['HOME']


def dup_item_for_dot_df(df, col_name, times_dup=3, sort=False):
    """
    Takes a DataFrame and a column name with items to be replicated. Sorts the list and replicates the number of
    times specified by the parameter times_dup. Copies the replicated values to the clip board.

    :param df: A DataFrame containing the column of values to be replicated.
    :param col_name: Name of the column containing values to replicate.
    :param times_dup: Number of times to replicate each value in the specified column.
    :param sort: Boolean to sort the replicated values.
    :type sort: bool
    """
    dup_list = []

    try:
        for item in df[col_name]:
            for i in range(times_dup):
                dup_list.append(item)

        a = pd.Series(dup_list)

        if sort:
            b = a.sort_values()
            return b
        else:
            return a
    except:
        print("The DataFrame does not have a " + col_name + " column.")


def spr_insert_images(tuple_list_imgs, worksheet, path_ss_img, path_senso_img):
    """
    Does the work of inserting the spr steady state and sensorgram images into the excel worksheet.
    :param tuple_list: List of tuples containing (steady state image, sensorgram image)
    :param worksheet: xlsxwriter object used to insert the images to a worksheet
    :param path_ss_img: Directory to the steady state images to insert.
    :param path_senso_img: Directory to the sensorgram images to insert.
    :return: None
    """
    # Format the rows and columns in the worksheet to fit the images.
    num_images = len(tuple_list_imgs)

    # Set height of each row
    for row in range(1, num_images + 1):
        worksheet.set_row(row=row, height=235)

    # Set the width of each column
    worksheet.set_column(first_col=3, last_col=4, width=58)

    row = 2
    for ss_img, senso_img in tuple_list_imgs:
        worksheet.insert_image('D' + str(row), path_ss_img + '/' + ss_img)
        worksheet.insert_image('E' + str(row), path_senso_img + '/' + senso_img)
        row += 1


# Using click to manage the command line interface
@click.command()
@click.option('--config_file', prompt="Please paste the path of the configuration file",
              help="Path of the configuration file. Text file with all of the file paths and meta "
                   "data for a particular experiment.")
@click.option('--save_file', prompt="Please type the name of the ADLP result file with an .xlsx extension",
              help="Name of the ADLP results file which is an Excel file.")
@click.option('--clip', is_flag=True,
              help="Option to indicate that the contents of the setup file are on the clipboard.")
def spr_create_dot_upload_file(config_file, save_file, clip):
    import configparser

    # ADLP save file path.
    if platform.system() == 'Windows':
        adlp_save_file_path = homedir + '\\Desktop\\' + save_file
    else:
        adlp_save_file_path = homedir + '/' + 'desktop' + '/' + save_file

    try:
        config_file = config_file.replace("\"", "")
        config = configparser.ConfigParser()
        config.read(config_file)

        # Get all of the file paths from the configuration file and store in variables so they are available
        if clip:
            df_cmpd_set = pd.read_clipboard()
        else:
            path_master_tbl = config.get('paths', 'path_mstr_tbl')
            df_cmpd_set = pd.read_csv(path_master_tbl)

        path_ss_img = config.get('paths', 'path_ss_img')
        path_ss_img = path_ss_img.replace("\"", "")
        path_senso_img = config.get('paths', 'path_senso_img')
        path_senso_img = path_senso_img.replace("\"", "")
        path_ss_txt = config.get('paths', 'path_ss_txt')
        path_ss_txt = path_ss_txt.replace("\"", "")
        path_senso_txt = config.get('paths', 'path_senso_txt')
        path_senso_txt = path_senso_txt.replace("\"", "")
        # Program does not currently use the report pt table.  This will change in the future.
        #path_report_pt = config.get('paths', 'path_report_pt')

        # Get all of the metadata variables
        num_fc_used = config.get('meta','num_fc_used')

        # Get the reference channel
        ref_fc_used = int(config.get('meta', 'ref_fc_used'))

        # Get the flow channels immobilized
        immobilized_fc = str(config.get('meta', 'immobilized_fc'))
        immobilized_fc = immobilized_fc.strip(" ")
        immobilized_fc = immobilized_fc.replace(' ', '')
        immobilized_fc_arr = immobilized_fc.split(',')
        immobilized_fc_arr = [int(i) for i in immobilized_fc_arr]

        if int(num_fc_used) != len(immobilized_fc_arr):
            raise RuntimeError ('The number of flow channels used is not equal to the number of immobilized flow '
                                'channels.')

        # Continue collecting variables from the configuration file.
        experiment_date = config.get('meta','experiment_date')
        project_code = config.get('meta','project_code')
        operator = config.get('meta','operator')
        instrument = config.get('meta','instrument')
        protocol = config.get('meta','protocol')
        chip_lot = config.get('meta','chip_lot')
        nucleotide = config.get('meta','nucleotide')
        raw_data_filename = config.get('meta','raw_data_filename')
        directory_folder = config.get('meta','directory_folder')
        fc2_protein_BIP = config.get('meta','fc2_protein_BIP')
        fc2_protein_MW = float(config.get('meta','fc2_protein_MW'))
        fc3_protein_BIP = config.get('meta','fc3_protein_BIP')
        fc3_protein_MW = float(config.get('meta','fc3_protein_MW'))
        fc4_protein_BIP = config.get('meta','fc4_protein_BIP')
        fc4_protein_MW = float(config.get('meta','fc4_protein_MW'))
    except:
        raise RuntimeError('Something is wrong with the config file. Please check.')

    # Start building the final Dotmatics DataFrame
    df_final_for_dot = pd.DataFrame()

    # Start by adding the Broad ID in the correct order.
    num_fc_used = int(num_fc_used)
    df_final_for_dot['BROAD_ID'] = pd.Series(dup_item_for_dot_df(df_cmpd_set, col_name='Broad ID',
                                                                 times_dup=num_fc_used))

    # Add the Project Code.  Get this from the config file.
    df_final_for_dot['PROJECT_CODE'] = project_code

    #  Add an empty column called curve_valid
    df_final_for_dot['CURVE_VALID'] = ''

    # Add an empty column called steady_state_img
    df_final_for_dot['SSC_STEADY_STATE_IMG'] = ''

    # Add an empty column called 1to1_img
    df_final_for_dot['SSC_IMAGE'] = ''

    # Add the starting compound concentrations
    df_final_for_dot['TOP_COMPOUND_UM'] = pd.Series(dup_item_for_dot_df(df_cmpd_set, col_name='Test [Cpd] uM',
                                                                 times_dup=num_fc_used))

    # Extract the RU Max for each compound using the report point file.
    df_final_for_dot['RU_TOP_CMPD'] = ''

    # Extract the steady state data and add to DataFrame
    # Read in the steady state text file into a DataFrame
    df_ss_txt = pd.read_csv(path_ss_txt, sep='\t')

    # Create new columns to sort the DataFrame as the original is out of order.
    df_ss_txt['sample_order'] = df_ss_txt['Image File'].str.split('_', expand=True)[1]
    df_ss_txt['sample_order'] = pd.to_numeric(df_ss_txt['sample_order'])
    df_ss_txt['fc_num'] = pd.to_numeric(df_ss_txt['Curve'].str[3])
    df_ss_txt = df_ss_txt.sort_values(by=['sample_order', 'fc_num'])
    df_ss_txt = df_ss_txt.reset_index(drop=True)
    df_ss_txt['KD_SS_UM'] = df_ss_txt['KD (M)'] * 1000000

    # Add the KD steady state
    df_final_for_dot['KD_SS_UM'] = df_ss_txt['KD_SS_UM']

    # Add the chi2_steady_state_affinity
    df_final_for_dot['CHI2_SS_AFFINITY'] = df_ss_txt['Chi² (RU²)']

    # Add the Fitted_Rmax_steady_state_affinity
    df_final_for_dot['FITTED_RMAX_SS_AFFINITY'] = df_ss_txt['Rmax (RU)']

    # Extract the sensorgram data and add to DataFrame
    # Read in the sensorgram data into a DataFrame
    df_senso_txt = pd.read_csv(path_senso_txt, sep='\t')
    df_senso_txt['sample_order'] = df_senso_txt['Image File'].str.split('_', expand=True)[1]
    df_senso_txt['sample_order'] = pd.to_numeric(df_senso_txt['sample_order'])
    df_senso_txt['fc_num'] = pd.to_numeric(df_senso_txt['Curve'].str[3])
    df_senso_txt = df_senso_txt.sort_values(by=['sample_order', 'fc_num'])
    df_senso_txt = df_senso_txt.reset_index(drop=True)

    # Add columns from df_senso_txt
    df_final_for_dot['KA_1_1_BINDING'] = df_senso_txt['ka (1/Ms)']
    df_final_for_dot['KD_LITTLE_1_1_BINDING'] = df_senso_txt['kd (1/s)']
    df_final_for_dot['KD_1_1_BINDING_UM'] = df_senso_txt['KD (M)'] * 1000000
    df_final_for_dot['chi2_1_1_binding'] = df_senso_txt['Chi² (RU²)']

    # Not sure what this is???
    df_final_for_dot['U_VALUE_1_1_BINDING'] = ''
    # Not sure what this is??

    # Continue creating new columns
    df_final_for_dot['FITTED_RMAX_1_1_BINDING'] = df_senso_txt['Rmax (RU)']
    df_final_for_dot['COMMENTS'] = ''

    # Rename the flow channels and add the flow channel column
    df_senso_txt['FC'] = df_senso_txt['Curve'].apply(lambda x: x.replace('c', 'C'))
    df_senso_txt['FC'] = df_senso_txt['FC'].apply(lambda x: x.replace('=', ''))
    df_senso_txt['FC'] = df_senso_txt['FC'].apply(lambda x: x.replace(' ', ''))
    df_final_for_dot['FC'] = df_senso_txt['FC']

    # Add protein RU
    # Need conditional if the reference channel is fc 3.
    if ref_fc_used == 3:

        # Add protein RU
        df_final_for_dot['PROTEIN_RU'] = 'Fill Manually'

        # Add protein MW
        protein_mw_dict = {'FC4-3Corr': fc4_protein_MW}
        df_final_for_dot['PROTEIN_MW'] = df_final_for_dot['FC'].map(protein_mw_dict)

        # Add BIP
        protein_bip_dict = {'FC4-3Corr': fc4_protein_BIP}
        df_final_for_dot['PROTEIN_ID'] = df_final_for_dot['FC'].map(protein_bip_dict)

    # Default is if the reference channel is 1.
    else:

        # Add protein RU
        df_final_for_dot['PROTEIN_RU'] = 'Fill Manually'

        # Add protein MW
        protein_mw_dict = {'FC2-1Corr': fc2_protein_MW, 'FC3-1Corr': fc3_protein_MW, 'FC4-1Corr': fc4_protein_MW}
        df_final_for_dot['PROTEIN_MW'] = df_final_for_dot['FC'].map(protein_mw_dict)

        # Add BIP
        protein_bip_dict = {'FC2-1Corr': fc2_protein_BIP, 'FC3-1Corr': fc3_protein_BIP, 'FC4-1Corr': fc4_protein_BIP}
        df_final_for_dot['PROTEIN_ID'] = df_final_for_dot['FC'].map(protein_bip_dict)

    # Add the MW for each compound.
    df_final_for_dot['MW'] = pd.Series(dup_item_for_dot_df(df_cmpd_set, col_name='MW',
                                                           times_dup=num_fc_used))

    # Continue adding columns to final DataFrame
    df_final_for_dot['INSTRUMENT'] = instrument
    df_final_for_dot['ASSAY_MODE'] = 'Single Cycle'
    df_final_for_dot['EXP_DATE'] = experiment_date
    df_final_for_dot['NUCLEOTIDE'] = nucleotide
    df_final_for_dot['CHIP_LOT'] = chip_lot
    df_final_for_dot['OPERATOR'] = operator
    df_final_for_dot['PROTOCOL_ID'] = protocol
    df_final_for_dot['RAW_DATA_FILE'] = raw_data_filename
    df_final_for_dot['DIR_FOLDER'] = directory_folder

    # Add the unique ID #
    df_final_for_dot['UNIQUE_ID'] = df_senso_txt['Sample'] + '_' + df_final_for_dot['FC'] + '_' + project_code + \
                                    '_' + experiment_date + \
                                    '_' + df_senso_txt['Image File'].str.split('_', expand=True)[5]

    # Add steady state image file path
    # Need to replace /Volumes with //Iron
    path_ss_img_edit = path_ss_img.replace('/Volumes', '//Iron')
    df_final_for_dot['SS_IMG_ID'] = path_ss_img_edit + '/' + df_ss_txt['Image File']

    # Add sensorgram image file path
    # Need to replace /Volumes with //Iron
    path_senso_img_edit = path_senso_img.replace('/Volumes', '//Iron')
    df_final_for_dot['SENSO_IMG_ID'] = path_senso_img_edit + '/' + df_senso_txt['Image File']

    # Add the Rmax_theoretical.
    # Note couldn't do this before as I needed to add protein MW and RU first.
    # As this varies for each cycle the user must fill this in manually for now.
    # df_final_for_dot['RMAX_THEORETICAL']
    # df_final_for_dot['RMAX_THEORETICAL'] = round((df_final_for_dot['MW'] / df_final_for_dot['PROTEIN_MW']) \
    #                                        * df_final_for_dot['PROTEIN_RU'], 2)
    df_final_for_dot['RMAX_THEORETICAL'] = 'Fill Manually'

    # Calculate Percent Binding
    # For single cycle kinetics this must be filled in manually
    # df_final_for_dot['%_BINDING_TOP'] = round((df_final_for_dot['RU_TOP_CMPD'] / df_final_for_dot[
    #     'RMAX_THEORETICAL']) * 100, 2)
    df_final_for_dot['%_BINDING_TOP'] = ''

    # Rearrange the columns for the final DataFrame (without images)
    df_final_for_dot = df_final_for_dot.loc[:, ['BROAD_ID', 'PROJECT_CODE', 'CURVE_VALID', 'SSC_STEADY_STATE_IMG',
       'SSC_IMAGE', 'TOP_COMPOUND_UM', 'RMAX_THEORETICAL', 'RU_TOP_CMPD', '%_BINDING_TOP', 'KD_SS_UM',
       'CHI2_SS_AFFINITY', 'FITTED_RMAX_SS_AFFINITY', 'KA_1_1_BINDING',
       'KD_LITTLE_1_1_BINDING', 'KD_1_1_BINDING_UM', 'chi2_1_1_binding',
       'U_VALUE_1_1_BINDING', 'FITTED_RMAX_1_1_BINDING', 'COMMENTS', 'FC',
       'PROTEIN_RU', 'PROTEIN_MW', 'PROTEIN_ID', 'MW', 'ASSAY_MODE', 'INSTRUMENT',
       'EXP_DATE', 'NUCLEOTIDE', 'CHIP_LOT', 'OPERATOR', 'PROTOCOL_ID',
       'RAW_DATA_FILE', 'DIR_FOLDER', 'UNIQUE_ID', 'SS_IMG_ID', 'SENSO_IMG_ID']]

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter(adlp_save_file_path, engine='xlsxwriter')

    # Convert the DataFrame to an XlsxWriter Excel object.
    df_final_for_dot.to_excel(writer, sheet_name='Sheet1', startcol=0, index=None)

    # Get the xlsxwriter workbook and worksheet objects.
    workbook = writer.book
    worksheet1 = writer.sheets['Sheet1']

    # Add a drop down list of comments.
    # Calculate the number of rows to add the drop down menu.
    num_cpds = len(df_cmpd_set.index)
    num_data_pts = (num_cpds * 3) + 1

    # Write the comments to the comment sheet.
    comments_list = pd.DataFrame({'Comments':
                                    ['Need to updated this list with single cycle kinetic comments']})

    # Convert comments list to DataFrame
    comments_list.to_excel(writer, sheet_name='Sheet2', startcol=0, index=0)

    # For larger drop down lists > 255 characters its necessary to create a list on a seperate worksheet.
    worksheet1.data_validation('S1:S' + str(num_data_pts),
                                    {'validate': 'list',
                                     'source': '=Sheet2!$A$2:$A$' + str(len(comments_list) + 1)
                                     })

    # Freeze the top row of the excel worksheet.
    worksheet1.freeze_panes(1, 0)

    # Add a cell format object to align text center.
    cell_format = workbook.add_format()
    cell_format.set_align('center')
    cell_format.set_align('vcenter')
    worksheet1.set_column('A:AJ', 25, cell_format)

    # Start preparing to insert the steady state and sensorgram images.
    # Get list of image files from df_ss_txt Dataframe.
    list_ss_img = df_ss_txt['Image File'].tolist()

    # Get list of images files in the df_senso_txt DataFrame.
    list_sonso_img = df_senso_txt['Image File'].tolist()

    # Create a list of tuples containing the names of the steady state image and sensorgram image.
    tuple_list_imgs = list(zip(list_ss_img, list_sonso_img))

    # Insert images into file.
    spr_insert_images(tuple_list_imgs, worksheet1, path_ss_img, path_senso_img)

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()
    print('Program Done!')
    print("The ADLP result was saved to your desktop.")


if __name__ == '__main__':
    spr_create_dot_upload_file()
