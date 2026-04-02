def register_user(username, late_comer_info):
    # Validate if the late-comer exists
    if not user_exists(late_comer_info['username']):
        raise ValueError("User does not exist, registration failed.")

    # Create the new user
    try:
        new_user = create_new_user(username)
    except Exception as e:
        return f"Error creating new user: {str(e)}"

    # Attempt to delete the late-comer, ensuring proper error handling
    try:
        delete_user(late_comer_info['username'])
    except Exception as delete_error:
        return f"Failed to delete user {late_comer_info['username']}: {str(delete_error)}"

    return new_user