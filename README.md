# Escobar Bot for Monitoring Swap Events

## Project Overview

This project is a Telegram bot designed to monitor and report swap events on multiple blockchains, including Ethereum, Binance Smart Chain (BSC), Base, TON, and Solana. The bot collects and provides real-time updates on swap transactions, offering users a convenient way to stay informed about market activities across different networks.

## Features

- **Multi-Blockchain Support**: Monitors swap events on Ethereum, BSC, Base, TON, and Solana.
- **Real-Time Notifications**: Sends instant notifications to users about swap events.
- **User Interaction**: Users can interact with the bot to get specific information or set preferences.
- **Media Handling**: Collects and sends user-provided media (GIFs, images, emojis).
- **Database Integration**: Saves and retrieves media files and user settings using a MySQL database.
- **User-Friendly Interface**: Provides a simple and intuitive interface for users to interact with the bot.

## Setup and Installation

### Prerequisites

- Python 3.7+
- MySQL database
- Telegram Bot API token

### Installation Steps

1. **Clone the Repository**:
   ```sh
   git clone https://github.com/TEESTIMONY/Escobar_bot.git
   cd Escobar_bot
   ```

2. **Install Python Dependencies**:
   ```sh
   pip install -r requirements.txt
   ```

3. **Configure MySQL Database**:
   - Create a MySQL database and a table for storing media files and user settings.
   - Update the `db_config` dictionary in your code with your MySQL database credentials.

   ```python
   db_config = {
       'user': 'your_db_user',
       'password': 'your_db_password',
       'host': 'your_db_host',
       'database': 'your_db_name',
   }
   ```

5. **Run the Bot**:
   ```sh
    main.py
   ```


## Usage

1. **Add the Bot to a Group**: 
   - Add the bot to your Telegram group.
   - Make the bot an admin of the group to allow it to send notifications and interact with users.

2. **Send a Token Address**:
   - Send a token address to the bot within the group.
   - The bot will start monitoring swap events for the provided token address and notify the group of any relevant transactions.

3. **Interact with the Bot**: 
   - Use the bot's commands to customize settings and manage media files.

## Commands

- `/start` - Start interacting with the bot.
- `/settings` - Configure your notification preferences.
- `/media` - Manage your media files.
- `/remove` - Remove a token with confirmation.
- `/add`    - Adds new token to the bot.

## Database Structure

- **Table `media`**:
  - `file_id` (VARCHAR)
  - `file_type` (VARCHAR)
  - `chat_id` (INT)
  - `created_at` (TIMESTAMP)

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or support, please contact testimonyalade191@gmail.com.

---
