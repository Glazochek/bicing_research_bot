import os
import csv
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram.error import NetworkError, TimedOut

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Reduce httpx logging noise
logging.getLogger('httpx').setLevel(logging.WARNING)

# CSV file configuration
CSV_FILE = 'research_data.csv'
CSV_COLUMNS = [
    'Serial ID',
    'Inventory Tag',
    'Pedaling Rate',
    'Left Brake Rate',
    'Right Brake Rate',
    'Tires Rate',
    'Appearence Rate',
    'Battery Level',
    'Is Straight Parking Angel',
    'Seat Hight',
    'Location',
    'Speed Rate',
    'Note',
    'Date'
]

# Conversation states - reordered with new fields
(SERIAL_ID, INVENTORY_TAG, LOCATION, PARKING_ANGEL, TIRES_RATE, SEAT_HEIGHT,
 APPEARENCE_RATE, BATTERY_LEVEL, LEFT_BRAKE_RATE, RIGHT_BRAKE_RATE, PEDALING_RATE,
 SPEED_RATE, NOTE, UPDATE_FIELD, UPDATE_VALUE) = range(15)


def initialize_csv():
    """Create CSV file with headers if it doesn't exist"""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
            writer.writeheader()


def read_csv():
    """Read all data from CSV"""
    initialize_csv()
    with open(CSV_FILE, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return list(reader)


def write_csv(data):
    """Write data to CSV"""
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(data)


def get_rate_keyboard():
    """Create keyboard for rate input (0-10) with Back and Skip"""
    return ReplyKeyboardMarkup(
        [['0', '1', '2', '3', '4'],
         ['5', '6', '7', '8', '9', '10'],
         ['Back', 'Skip']],
        one_time_keyboard=True,
        resize_keyboard=True
    )


def get_battery_keyboard():
    """Create keyboard for battery level (0-4) with Back and Skip"""
    return ReplyKeyboardMarkup(
        [['0', '1', '2', '3', '4'],
         ['Back', 'Skip']],
        one_time_keyboard=True,
        resize_keyboard=True
    )


def get_boolean_keyboard():
    """Create keyboard for true/false input with Back and Skip"""
    return ReplyKeyboardMarkup(
        [['True', 'False'],
         ['Back', 'Skip']],
        one_time_keyboard=True,
        resize_keyboard=True
    )


def get_seat_height_keyboard():
    """Create keyboard for seat height (1-10) with Back and Skip"""
    return ReplyKeyboardMarkup(
        [['1', '2', '3', '4', '5'],
         ['6', '7', '8', '9', '10'],
         ['Back', 'Skip']],
        one_time_keyboard=True,
        resize_keyboard=True
    )


def get_location_keyboard():
    """Create keyboard with location request button, Back and Skip"""
    keyboard = [
        [KeyboardButton("Share Location", request_location=True)],
        ['Back', 'Skip']
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def get_serial_id_keyboard():
    """Create keyboard for Serial ID with only Cancel"""
    return ReplyKeyboardMarkup(
        [['Cancel']],
        one_time_keyboard=True,
        resize_keyboard=True
    )


def get_text_input_keyboard():
    """Create keyboard for text input with Back and Skip"""
    return ReplyKeyboardMarkup(
        [['Back', 'Skip']],
        one_time_keyboard=True,
        resize_keyboard=True
    )


def get_note_keyboard():
    """Create keyboard for Note with Back and Skip"""
    return ReplyKeyboardMarkup(
        [['Back', 'Skip']],
        one_time_keyboard=True,
        resize_keyboard=True
    )


def format_summary(data):
    """Format research data as a summary"""
    summary = "Summary:\n\n"
    for key, value in data.items():
        summary += f"{key}: {value}\n"
    return summary


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    await update.message.reply_text(
        "Bike Research Bot\n\n"
        "Commands:\n"
        "/add - Add new record\n"
        "/delete <Serial ID> - Delete record\n"
        "/update <Serial ID> - Update record\n"
        "/see - Download CSV file\n"
        "/cancel - Cancel operation"
    )


async def add_start(update: Update, context:  ContextTypes.DEFAULT_TYPE):
    """Start the add conversation"""
    context.user_data['research_data'] = {}
    await update.message.reply_text(
        "Enter Serial ID:",
        reply_markup=get_serial_id_keyboard()
    )
    return SERIAL_ID


async def add_serial_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store Serial ID and ask for Inventory Tag"""
    if update.message.text == 'Cancel':
        context.user_data. clear()
        await update.message. reply_text("Cancelled", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    
    context.user_data['research_data']['Serial ID'] = update.message.text
    await update.message.reply_text(
        "Enter Inventory Tag:",
        reply_markup=get_text_input_keyboard()
    )
    return INVENTORY_TAG


async def add_inventory_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store Inventory Tag and ask for Location"""
    if update.message. text == 'Skip':
        # Only set N/A if not already set
        if 'Inventory Tag' not in context.user_data['research_data']: 
            context.user_data['research_data']['Inventory Tag'] = 'N/A'
    elif update.message.text == 'Back':
        await update.message.reply_text(
            "Enter Serial ID:",
            reply_markup=get_serial_id_keyboard()
        )
        return SERIAL_ID
    else:
        context.user_data['research_data']['Inventory Tag'] = update.message.text
    
    await update.message.reply_text(
        "Location:",
        reply_markup=get_location_keyboard()
    )
    return LOCATION


async def add_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store Location and ask for Parking Angel"""
    if update.message.text == 'Skip':
        # Only set N/A if not already set
        if 'Location' not in context.user_data['research_data']:
            context.user_data['research_data']['Location'] = 'N/A'
    elif update.message.text == 'Back':
        await update.message.reply_text(
            "Enter Inventory Tag:",
            reply_markup=get_text_input_keyboard()
        )
        return INVENTORY_TAG
    elif update.message.location: 
        latitude = update.message.location.latitude
        longitude = update.message. location.longitude
        location_text = f"{latitude}, {longitude}"
        context.user_data['research_data']['Location'] = location_text
    else:
        await update.message.reply_text("Please share location or skip:")
        return LOCATION
    
    await update. message.reply_text(
        "Is Straight Parking Angel? ",
        reply_markup=get_boolean_keyboard()
    )
    return PARKING_ANGEL


async def add_parking_angel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store Parking Angel and ask for Tires Rate"""
    if update.message. text == 'Skip':
        # Only set N/A if not already set
        if 'Is Straight Parking Angel' not in context.user_data['research_data']:
            context.user_data['research_data']['Is Straight Parking Angel'] = 'N/A'
    elif update.message.text == 'Back':
        await update.message. reply_text(
            "Location:",
            reply_markup=get_location_keyboard()
        )
        return LOCATION
    else:
        text = update.message.text. lower()
        if text not in ['true', 'false']: 
            await update.message.reply_text("Select 'True' or 'False':")
            return PARKING_ANGEL
        context.user_data['research_data']['Is Straight Parking Angel'] = text
    
    await update.message.reply_text(
        "Tires Rate (0-10):",
        reply_markup=get_rate_keyboard()
    )
    return TIRES_RATE


async def add_tires_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store Tires Rate and ask for Seat Height"""
    if update.message.text == 'Skip': 
        # Only set N/A if not already set
        if 'Tires Rate' not in context.user_data['research_data']:
            context.user_data['research_data']['Tires Rate'] = 'N/A'
    elif update.message. text == 'Back':
        await update.message.reply_text(
            "Is Straight Parking Angel?",
            reply_markup=get_boolean_keyboard()
        )
        return PARKING_ANGEL
    else:
        if not update.message.text.isdigit() or int(update.message.text) < 0 or int(update.message.text) > 10:
            await update.message.reply_text("Select a valid rate (0-10):")
            return TIRES_RATE
        context.user_data['research_data']['Tires Rate'] = update.message.text
    
    await update.message.reply_text(
        "Seat Hight (1-10):",
        reply_markup=get_seat_height_keyboard()
    )
    return SEAT_HEIGHT


async def add_seat_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store Seat Height and ask for Appearence Rate"""
    if update. message.text == 'Skip': 
        # Only set N/A if not already set
        if 'Seat Hight' not in context.user_data['research_data']:
            context.user_data['research_data']['Seat Hight'] = 'N/A'
    elif update.message.text == 'Back':
        await update.message. reply_text(
            "Tires Rate (0-10):",
            reply_markup=get_rate_keyboard()
        )
        return TIRES_RATE
    else:
        if not update.message.text.isdigit() or int(update.message.text) < 1 or int(update.message. text) > 10:
            await update.message.reply_text("Select a valid height (1-10):")
            return SEAT_HEIGHT
        context.user_data['research_data']['Seat Hight'] = update.message.text
    
    await update.message.reply_text(
        "Appearence Rate (0-10):",
        reply_markup=get_rate_keyboard()
    )
    return APPEARENCE_RATE


async def add_appearence_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store Appearence Rate and ask for Battery Level"""
    if update.message.text == 'Skip':
        # Only set N/A if not already set
        if 'Appearence Rate' not in context.user_data['research_data']: 
            context.user_data['research_data']['Appearence Rate'] = 'N/A'
    elif update.message.text == 'Back':
        await update.message.reply_text(
            "Seat Hight (1-10):",
            reply_markup=get_seat_height_keyboard()
        )
        return SEAT_HEIGHT
    else:
        if not update.message.text.isdigit() or int(update.message. text) < 0 or int(update.message.text) > 10:
            await update. message.reply_text("Select a valid rate (0-10):")
            return APPEARENCE_RATE
        context.user_data['research_data']['Appearence Rate'] = update.message.text
    
    await update.message.reply_text(
        "Battery Level (0-4):",
        reply_markup=get_battery_keyboard()
    )
    return BATTERY_LEVEL


async def add_battery_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store Battery Level and ask for Left Brake Rate"""
    if update.message.text == 'Skip':
        # Only set N/A if not already set
        if 'Battery Level' not in context.user_data['research_data']:
            context.user_data['research_data']['Battery Level'] = 'N/A'
    elif update.message.text == 'Back':
        await update.message.reply_text(
            "Appearence Rate (0-10):",
            reply_markup=get_rate_keyboard()
        )
        return APPEARENCE_RATE
    else:
        if not update.message.text.isdigit() or int(update.message. text) < 0 or int(update.message.text) > 4:
            await update. message.reply_text("Select a valid battery level (0-4):")
            return BATTERY_LEVEL
        context.user_data['research_data']['Battery Level'] = update.message.text
    
    await update.message.reply_text(
        "Left Brake Rate (0-10):",
        reply_markup=get_rate_keyboard()
    )
    return LEFT_BRAKE_RATE


async def add_left_brake_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store Left Brake Rate and ask for Right Brake Rate"""
    if update.message.text == 'Skip': 
        # Only set N/A if not already set
        if 'Left Brake Rate' not in context.user_data['research_data']:
            context.user_data['research_data']['Left Brake Rate'] = 'N/A'
    elif update.message. text == 'Back':
        await update.message.reply_text(
            "Battery Level (0-4):",
            reply_markup=get_battery_keyboard()
        )
        return BATTERY_LEVEL
    else:
        if not update. message.text.isdigit() or int(update.message.text) < 0 or int(update.message.text) > 10:
            await update.message. reply_text("Select a valid rate (0-10):")
            return LEFT_BRAKE_RATE
        context.user_data['research_data']['Left Brake Rate'] = update.message.text
    
    await update.message. reply_text(
        "Right Brake Rate (0-10):",
        reply_markup=get_rate_keyboard()
    )
    return RIGHT_BRAKE_RATE


async def add_right_brake_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store Right Brake Rate and ask for Pedaling Rate"""
    if update. message.text == 'Skip': 
        # Only set N/A if not already set
        if 'Right Brake Rate' not in context.user_data['research_data']:
            context.user_data['research_data']['Right Brake Rate'] = 'N/A'
    elif update.message.text == 'Back': 
        await update.message.reply_text(
            "Left Brake Rate (0-10):",
            reply_markup=get_rate_keyboard()
        )
        return LEFT_BRAKE_RATE
    else:
        if not update.message.text.isdigit() or int(update.message.text) < 0 or int(update.message.text) > 10:
            await update.message.reply_text("Select a valid rate (0-10):")
            return RIGHT_BRAKE_RATE
        context.user_data['research_data']['Right Brake Rate'] = update.message.text
    
    await update.message.reply_text(
        "Pedaling Rate (0-10):",
        reply_markup=get_rate_keyboard()
    )
    return PEDALING_RATE


async def add_pedaling_rate(update:  Update, context: ContextTypes. DEFAULT_TYPE):
    """Store Pedaling Rate and ask for Speed Rate"""
    if update.message.text == 'Skip': 
        # Only set N/A if not already set
        if 'Pedaling Rate' not in context.user_data['research_data']:
            context.user_data['research_data']['Pedaling Rate'] = 'N/A'
    elif update.message. text == 'Back':
        await update.message.reply_text(
            "Right Brake Rate (0-10):",
            reply_markup=get_rate_keyboard()
        )
        return RIGHT_BRAKE_RATE
    else:
        if not update.message.text. isdigit() or int(update.message.text) < 0 or int(update.message. text) > 10:
            await update.message.reply_text("Select a valid rate (0-10):")
            return PEDALING_RATE
        context. user_data['research_data']['Pedaling Rate'] = update. message.text
    
    await update.message.reply_text(
        "Speed Rate (0-10):",
        reply_markup=get_rate_keyboard()
    )
    return SPEED_RATE


async def add_speed_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store Speed Rate and ask for Note"""
    if update.message.text == 'Skip':
        # Only set N/A if not already set
        if 'Speed Rate' not in context.user_data['research_data']:
            context.user_data['research_data']['Speed Rate'] = 'N/A'
    elif update.message.text == 'Back':
        await update.message.reply_text(
            "Pedaling Rate (0-10):",
            reply_markup=get_rate_keyboard()
        )
        return PEDALING_RATE
    else: 
        if not update.message. text.isdigit() or int(update.message.text) < 0 or int(update. message.text) > 10:
            await update.message.reply_text("Select a valid rate (0-10):")
            return SPEED_RATE
        context.user_data['research_data']['Speed Rate'] = update.message.text
    
    await update.message.reply_text(
        "Any notes?",
        reply_markup=get_note_keyboard()
    )
    return NOTE


async def add_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store Note, add timestamp, show summary, and save to CSV"""
    if update. message.text == 'Skip': 
        # Only set N/A if not already set
        if 'Note' not in context.user_data['research_data']: 
            context.user_data['research_data']['Note'] = 'N/A'
    elif update.message.text == 'Back':
        await update.message. reply_text(
            "Speed Rate (0-10):",
            reply_markup=get_rate_keyboard()
        )
        return SPEED_RATE
    else:
        context.user_data['research_data']['Note'] = update.message. text
    
    # Automatically add current date and time
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    context.user_data['research_data']['Date'] = current_datetime
    
    # Show summary
    summary = format_summary(context.user_data['research_data'])
    await update.message.reply_text(
        summary,
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Save to CSV
    data = read_csv()
    data.append(context.user_data['research_data'])
    write_csv(data)
    
    await update.message.reply_text("Saved")
    
    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a record by Serial ID"""
    if not context.args:
        await update.message. reply_text("Usage: /delete <Serial ID>")
        return
    
    serial_id = ' '.join(context.args)
    data = read_csv()
    
    # Find and remove the record
    original_length = len(data)
    data = [row for row in data if row['Serial ID'] != serial_id]
    
    if len(data) < original_length:
        write_csv(data)
        await update.message.reply_text(f"Deleted '{serial_id}'")
    else:
        await update.message.reply_text(f"Not found '{serial_id}'")


async def update_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the update conversation"""
    if not context.args:
        await update.message. reply_text("Usage: /update <Serial ID>")
        return ConversationHandler.END
    
    serial_id = ' '.join(context.args)
    data = read_csv()
    
    # Find the record
    record = None
    for row in data: 
        if row['Serial ID'] == serial_id:
            record = row
            break
    
    if not record:
        await update.message.reply_text(f"Not found '{serial_id}'")
        return ConversationHandler.END
    
    context.user_data['update_serial_id'] = serial_id
    context.user_data['update_record'] = record
    
    # Create keyboard with column names (excluding Serial ID and Date)
    columns = [col for col in CSV_COLUMNS if col not in ['Serial ID', 'Date']]
    keyboard = [[col] for col in columns]
    keyboard.append(['Cancel'])
    
    await update.message.reply_text(
        f"Update field for '{serial_id}':",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return UPDATE_FIELD


async def update_field(update: Update, context:  ContextTypes.DEFAULT_TYPE):
    """Store the field to update and ask for new value"""
    field = update.message.text
    
    if field == 'Cancel': 
        context.user_data. clear()
        await update.message.reply_text("Cancelled", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    
    if field not in CSV_COLUMNS or field in ['Serial ID', 'Date']: 
        await update.message.reply_text("Invalid field")
        return UPDATE_FIELD
    
    context.user_data['update_field'] = field
    
    # Show appropriate keyboard based on field type
    if field in ['Pedaling Rate', 'Left Brake Rate', 'Right Brake Rate',
                 'Tires Rate', 'Appearence Rate', 'Speed Rate']: 
        keyboard = get_rate_keyboard()
        message = f"New {field} (0-10):"
    elif field == 'Battery Level':
        keyboard = get_battery_keyboard()
        message = f"New {field} (0-4):"
    elif field == 'Is Straight Parking Angel': 
        keyboard = get_boolean_keyboard()
        message = f"New {field}:"
    elif field == 'Seat Hight':
        keyboard = get_seat_height_keyboard()
        message = f"New {field} (1-10):"
    elif field == 'Location':
        keyboard = get_location_keyboard()
        message = "New Location:"
    else:  # Note or Inventory Tag
        keyboard = get_text_input_keyboard()
        message = f"New {field}:"
    
    await update.message. reply_text(message, reply_markup=keyboard)
    return UPDATE_VALUE


async def update_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update the field value in CSV"""
    if update.message.text == 'Skip':
        value = 'N/A'
    elif update.message.text == 'Back':
        serial_id = context.user_data['update_serial_id']
        columns = [col for col in CSV_COLUMNS if col not in ['Serial ID', 'Date']]
        keyboard = [[col] for col in columns]
        keyboard.append(['Cancel'])
        
        await update.message.reply_text(
            f"Update field for '{serial_id}':",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return UPDATE_FIELD
    else:
        field = context.user_data['update_field']
        
        # Handle location specially
        if field == 'Location':
            if update.message.location:
                latitude = update.message.location.latitude
                longitude = update.message.location.longitude
                value = f"{latitude}, {longitude}"
            else:
                await update.message.reply_text("Share location or skip:")
                return UPDATE_VALUE
        elif field in ['Note', 'Inventory Tag']: 
            # Note and Inventory Tag can be any text
            value = update.message.text
        else:
            value = update.message.text
            
            # Validate input
            if field in ['Pedaling Rate', 'Left Brake Rate', 'Right Brake Rate',
                         'Tires Rate', 'Appearence Rate', 'Speed Rate']:
                if not value. isdigit() or int(value) < 0 or int(value) > 10:
                    await update.message.reply_text("Select a valid rate (0-10):")
                    return UPDATE_VALUE
            elif field == 'Battery Level':
                if not value.isdigit() or int(value) < 0 or int(value) > 4:
                    await update.message.reply_text("Select a valid battery level (0-4):")
                    return UPDATE_VALUE
            elif field == 'Is Straight Parking Angel':
                if value.lower() not in ['true', 'false']:
                    await update.message.reply_text("Select 'True' or 'False':")
                    return UPDATE_VALUE
                value = value.lower()
            elif field == 'Seat Hight':
                if not value.isdigit() or int(value) < 1 or int(value) > 10:
                    await update.message.reply_text("Select a valid height (1-10):")
                    return UPDATE_VALUE
    
    # Update the record
    field = context.user_data['update_field']
    serial_id = context.user_data['update_serial_id']
    data = read_csv()
    
    for row in data:
        if row['Serial ID'] == serial_id:
            row[field] = value
            break
    
    write_csv(data)
    
    await update.message.reply_text(
        "Updated",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END


async def see_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send CSV file"""
    data = read_csv()
    
    if not data:
        await update.message.reply_text("No records")
        return
    
    # Send the CSV file
    try: 
        with open(CSV_FILE, 'rb') as file:
            await update.message.reply_document(
                document=file,
                filename=CSV_FILE,
                caption=f"{len(data)} records"
            )
    except Exception as e:
        logger.error(f"Error sending file: {e}")
        await update.message.reply_text("Error sending file")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current conversation"""
    context.user_data.clear()
    await update.message.reply_text(
        "Cancelled",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def error_handler(update: Update, context:  ContextTypes.DEFAULT_TYPE):
    """Log errors and handle network issues gracefully"""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Don't notify user for network errors - they're temporary
    if isinstance(context.error, (NetworkError, TimedOut)):
        return
    
    # For other errors, try to notify the user
    try:
        if update and update.effective_message:
            await update. effective_message.reply_text(
                "An error occurred. Please try again."
            )
    except Exception: 
        pass


def main():
    """Start the bot"""
    # Initialize CSV file
    initialize_csv()
    
    # Get bot token from environment variable
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("Error: Please set TELEGRAM_BOT_TOKEN environment variable")
        print("Example: export TELEGRAM_BOT_TOKEN='your-bot-token-here'")
        return
    
    # Create application with increased timeouts for better network resilience
    application = (
        Application.builder()
        .token(token)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )
    
    # Add conversation handler for adding records
    add_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add_start)],
        states={
            SERIAL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_serial_id)],
            INVENTORY_TAG: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_inventory_tag)],
            LOCATION: [
                MessageHandler(filters. LOCATION, add_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_location)
            ],
            PARKING_ANGEL:  [MessageHandler(filters.TEXT & ~filters.COMMAND, add_parking_angel)],
            TIRES_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_tires_rate)],
            SEAT_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_seat_height)],
            APPEARENCE_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_appearence_rate)],
            BATTERY_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_battery_level)],
            LEFT_BRAKE_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_left_brake_rate)],
            RIGHT_BRAKE_RATE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, add_right_brake_rate)],
            PEDALING_RATE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, add_pedaling_rate)],
            SPEED_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_speed_rate)],
            NOTE: [MessageHandler(filters.TEXT & ~filters. COMMAND, add_note)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Add conversation handler for updating records
    update_handler = ConversationHandler(
        entry_points=[CommandHandler('update', update_start)],
        states={
            UPDATE_FIELD: [MessageHandler(filters.TEXT & ~filters. COMMAND, update_field)],
            UPDATE_VALUE: [
                MessageHandler(filters. LOCATION, update_value),
                MessageHandler(filters.TEXT & ~filters.COMMAND, update_value)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(add_handler)
    application.add_handler(CommandHandler('delete', delete_command))
    application.add_handler(update_handler)
    application.add_handler(CommandHandler('see', see_command))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    print("Bot running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == '__main__':
    main()
