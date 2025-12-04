"""OnlyFans Account Information

Get creator account information for OnlyFans
"""

from config.onlyfans_config import OnlyFansConfig
from download.downloadstate import DownloadState
from textio import print_info, print_error


def get_creator_account_info(config: OnlyFansConfig, state: DownloadState) -> None:
    """
    Get and display creator account information

    Args:
        config: OnlyFans configuration
        state: Download state for this creator

    Raises:
        RuntimeError: If unable to fetch creator info
    """
    try:
        api = config.get_api()

        print_info(f"Fetching account info for: {state.creator_name}")

        # Get user info by username
        user_data = api.get_user_by_username(state.creator_name)

        # Store creator ID for downloads
        state.account_id = str(user_data.get('id'))
        state.creator_name = user_data.get('username', state.creator_name)

        # Display info
        print_info(f"Creator: {user_data.get('name', 'N/A')}")
        print_info(f"Username: @{state.creator_name}")
        print_info(f"ID: {state.account_id}")

        if 'avatar' in user_data:
            print_info(f"Has avatar: Yes")

        # Check subscription status if available
        if 'subscribedBy' in user_data:
            is_subscribed = user_data['subscribedBy']
            if is_subscribed:
                print_info("Subscription: Active ✓")
            else:
                print_error("Warning: Not subscribed to this creator")

    except Exception as e:
        raise RuntimeError(f"Failed to get account info for {state.creator_name}: {e}")
