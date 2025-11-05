import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Avatar,
  Card,
  CardContent,
  Divider,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  Switch,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  InputAdornment
} from '@mui/material';
import {
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon
} from '@mui/icons-material';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'react-toastify';
import axios from 'axios';
import LoadingSpinner from '../components/Common/LoadingSpinner';

const ProfilePage = () => {
  const { user, updateProfile } = useAuth();

  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState(false);
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Profile form validation
  const profileValidationSchema = Yup.object({
    name: Yup.string()
      .min(2, 'Name must be at least 2 characters')
      .max(50, 'Name must not exceed 50 characters')
      .required('Name is required'),
    age: Yup.number()
      .min(13, 'Age must be at least 13')
      .max(120, 'Please enter a valid age')
      .nullable(),
    gender: Yup.string().nullable(),
    phone: Yup.string()
      .matches(/^[\+]?[1-9][\d]{0,15}$/, 'Invalid phone number format')
      .nullable()
  });

  // Password change validation
  const passwordValidationSchema = Yup.object({
    currentPassword: Yup.string()
      .required('Current password is required'),
    newPassword: Yup.string()
      .min(8, 'Password must be at least 8 characters')
      .matches(
        /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
        'Password must contain at least one uppercase letter, one lowercase letter, and one number'
      )
      .required('New password is required'),
    confirmPassword: Yup.string()
      .oneOf([Yup.ref('newPassword'), null], 'Passwords must match')
      .required('Please confirm your new password')
  });

  // Profile form
  const profileFormik = useFormik({
    initialValues: {
      name: user?.name || '',
      age: user?.age || '',
      gender: user?.gender || '',
      phone: user?.phone || ''
    },
    validationSchema: profileValidationSchema,
    enableReinitialize: true,
    onSubmit: async (values) => {
      setLoading(true);
      try {
        const result = await updateProfile(values);
        if (result.success) {
          setEditing(false);
          toast.success('Profile updated successfully');
        }
      } catch (error) {
        toast.error('Failed to update profile');
      } finally {
        setLoading(false);
      }
    }
  });

  // Password form
  const passwordFormik = useFormik({
    initialValues: {
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    },
    validationSchema: passwordValidationSchema,
    onSubmit: async (values) => {
      setLoading(true);
      try {
        const response = await axios.post('/auth/change-password', {
          current_password: values.currentPassword,
          new_password: values.newPassword
        });

        toast.success('Password changed successfully');
        setShowPasswordDialog(false);
        passwordFormik.resetForm();
      } catch (error) {
        toast.error(error.response?.data?.error || 'Failed to change password');
      } finally {
        setLoading(false);
      }
    }
  });

  const handleCancelEdit = () => {
    profileFormik.resetForm();
    setEditing(false);
  };

  const handleDeleteAccount = async () => {
    try {
      setLoading(true);
      await axios.delete('/auth/delete-account');
      toast.success('Account deleted successfully');
      // Redirect to home page after successful deletion
      window.location.href = '/';
    } catch (error) {
      toast.error('Failed to delete account');
    } finally {
      setLoading(false);
      setShowDeleteDialog(false);
    }
  };

  const handleExportData = async () => {
    try {
      const response = await axios.get('/profile/export', {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `my-health-data-${new Date().toISOString().split('T')[0]}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      toast.success('Data exported successfully');
    } catch (error) {
      toast.error('Failed to export data');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (!user) {
    return <LoadingSpinner fullScreen message="Loading profile..." />;
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography variant="h4" component="h1" fontWeight="bold" sx={{ mb: 1 }}>
          👤 My Profile
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Manage your account information and preferences
        </Typography>
      </Box>

      <Grid container spacing={4}>
        {/* Profile Information */}
        <Grid item xs={12} md={8}>
          <Paper elevation={2} sx={{ p: 4 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6" fontWeight="bold">
                Profile Information
              </Typography>
              <Button
                variant={editing ? "outlined" : "contained"}
                startIcon={editing ? <CancelIcon /> : <EditIcon />}
                onClick={editing ? handleCancelEdit : () => setEditing(true)}
                disabled={loading}
              >
                {editing ? 'Cancel' : 'Edit Profile'}
              </Button>
            </Box>

            <Box component="form" onSubmit={profileFormik.handleSubmit}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    id="name"
                    name="name"
                    label="Full Name"
                    value={profileFormik.values.name}
                    onChange={profileFormik.handleChange}
                    onBlur={profileFormik.handleBlur}
                    error={profileFormik.touched.name && Boolean(profileFormik.errors.name)}
                    helperText={profileFormik.touched.name && profileFormik.errors.name}
                    disabled={!editing || loading}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    id="age"
                    name="age"
                    label="Age"
                    type="number"
                    value={profileFormik.values.age}
                    onChange={profileFormik.handleChange}
                    onBlur={profileFormik.handleBlur}
                    error={profileFormik.touched.age && Boolean(profileFormik.errors.age)}
                    helperText={profileFormik.touched.age && profileFormik.errors.age}
                    disabled={!editing || loading}
                    inputProps={{ min: 13, max: 120 }}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControl
                    fullWidth
                    error={profileFormik.touched.gender && Boolean(profileFormik.errors.gender)}
                    disabled={!editing || loading}
                  >
                    <InputLabel>Gender</InputLabel>
                    <Select
                      id="gender"
                      name="gender"
                      value={profileFormik.values.gender}
                      label="Gender"
                      onChange={profileFormik.handleChange}
                      onBlur={profileFormik.handleBlur}
                    >
                      <MenuItem value="">
                        <em>Prefer not to say</em>
                      </MenuItem>
                      <MenuItem value="Male">Male</MenuItem>
                      <MenuItem value="Female">Female</MenuItem>
                      <MenuItem value="Other">Other</MenuItem>
                    </Select>
                    {profileFormik.touched.gender && profileFormik.errors.gender && (
                      <FormHelperText>{profileFormik.errors.gender}</FormHelperText>
                    )}
                  </FormControl>
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    id="phone"
                    name="phone"
                    label="Phone Number"
                    type="tel"
                    value={profileFormik.values.phone}
                    onChange={profileFormik.handleChange}
                    onBlur={profileFormik.handleBlur}
                    error={profileFormik.touched.phone && Boolean(profileFormik.errors.phone)}
                    helperText={profileFormik.touched.phone && profileFormik.errors.phone}
                    disabled={!editing || loading}
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Email Address"
                    value={user.email}
                    disabled
                    helperText="Email address cannot be changed"
                  />
                </Grid>

                {editing && (
                  <Grid item xs={12}>
                    <Button
                      type="submit"
                      variant="contained"
                      startIcon={<SaveIcon />}
                      disabled={loading || !profileFormik.isValid || !profileFormik.dirty}
                      fullWidth
                    >
                      {loading ? 'Saving...' : 'Save Changes'}
                    </Button>
                  </Grid>
                )}
              </Grid>
            </Box>
          </Paper>
        </Grid>

        {/* Profile Summary */}
        <Grid item xs={12} md={4}>
          <Paper elevation={2} sx={{ p: 3, textAlign: 'center', mb: 3 }}>
            <Avatar
              sx={{
                width: 80,
                height: 80,
                margin: '0 auto 16px',
                backgroundColor: 'primary.main',
                fontSize: '2rem'
              }}
            >
              {user.name?.charAt(0)?.toUpperCase() || 'U'}
            </Avatar>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 1 }}>
              {user.name}
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              {user.email}
            </Typography>
            <Chip
              label={user.auth_provider === 'google' ? 'Google Account' : 'Email Account'}
              color="primary"
              variant="outlined"
              size="small"
            />
          </Paper>

          {/* Account Info */}
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
              Account Information
            </Typography>
            <List dense>
              <ListItem sx={{ px: 0 }}>
                <ListItemText
                  primary="Member Since"
                  secondary={formatDate(user.created_at)}
                />
              </ListItem>
              <ListItem sx={{ px: 0 }}>
                <ListItemText
                  primary="Last Login"
                  secondary={formatDate(user.last_login)}
                />
              </ListItem>
              <ListItem sx={{ px: 0 }}>
                <ListItemText
                  primary="Account Status"
                  secondary={
                    <Chip
                      label={user.is_active ? 'Active' : 'Inactive'}
                      color={user.is_active ? 'success' : 'error'}
                      size="small"
                    />
                  }
                />
              </ListItem>
              <ListItem sx={{ px: 0 }}>
                <ListItemText
                  primary="Email Verified"
                  secondary={
                    <Chip
                      label={user.is_verified ? 'Verified' : 'Unverified'}
                      color={user.is_verified ? 'success' : 'warning'}
                      size="small"
                    />
                  }
                />
              </ListItem>
            </List>
          </Paper>
        </Grid>

        {/* Security Settings */}
        <Grid item xs={12}>
          <Paper elevation={2} sx={{ p: 4 }}>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 3 }}>
              Security & Privacy
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={4}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<SecurityIcon />}
                  onClick={() => setShowPasswordDialog(true)}
                  disabled={user.auth_provider === 'google'}
                >
                  Change Password
                </Button>
                {user.auth_provider === 'google' && (
                  <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                    Google accounts use Google's password management
                  </Typography>
                )}
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={handleExportData}
                >
                  Export My Data
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Button
                  fullWidth
                  variant="outlined"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={() => setShowDeleteDialog(true)}
                >
                  Delete Account
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>

      {/* Change Password Dialog */}
      <Dialog open={showPasswordDialog} onClose={() => setShowPasswordDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Change Password</DialogTitle>
        <DialogContent>
          <Box component="form" onSubmit={passwordFormik.handleSubmit} sx={{ mt: 2 }}>
            <TextField
              fullWidth
              id="currentPassword"
              name="currentPassword"
              label="Current Password"
              type={showPassword ? 'text' : 'password'}
              value={passwordFormik.values.currentPassword}
              onChange={passwordFormik.handleChange}
              onBlur={passwordFormik.handleBlur}
              error={passwordFormik.touched.currentPassword && Boolean(passwordFormik.errors.currentPassword)}
              helperText={passwordFormik.touched.currentPassword && passwordFormik.errors.currentPassword}
              sx={{ mb: 3 }}
              InputProps={{
                endAdornment: (
                  <IconButton
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                  </IconButton>
                )
              }}
            />

            <TextField
              fullWidth
              id="newPassword"
              name="newPassword"
              label="New Password"
              type={showNewPassword ? 'text' : 'password'}
              value={passwordFormik.values.newPassword}
              onChange={passwordFormik.handleChange}
              onBlur={passwordFormik.handleBlur}
              error={passwordFormik.touched.newPassword && Boolean(passwordFormik.errors.newPassword)}
              helperText={passwordFormik.touched.newPassword && passwordFormik.errors.newPassword}
              sx={{ mb: 3 }}
              InputProps={{
                endAdornment: (
                  <IconButton
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    edge="end"
                  >
                    {showNewPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                  </IconButton>
                )
              }}
            />

            <TextField
              fullWidth
              id="confirmPassword"
              name="confirmPassword"
              label="Confirm New Password"
              type={showConfirmPassword ? 'text' : 'password'}
              value={passwordFormik.values.confirmPassword}
              onChange={passwordFormik.handleChange}
              onBlur={passwordFormik.handleBlur}
              error={passwordFormik.touched.confirmPassword && Boolean(passwordFormik.errors.confirmPassword)}
              helperText={passwordFormik.touched.confirmPassword && passwordFormik.errors.confirmPassword}
              InputProps={{
                endAdornment: (
                  <IconButton
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    edge="end"
                  >
                    {showConfirmPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                  </IconButton>
                )
              }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPasswordDialog(false)}>Cancel</Button>
          <Button
            onClick={passwordFormik.handleSubmit}
            variant="contained"
            disabled={loading || !passwordFormik.isValid || !passwordFormik.dirty}
          >
            {loading ? 'Changing...' : 'Change Password'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Account Dialog */}
      <Dialog open={showDeleteDialog} onClose={() => setShowDeleteDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle color="error">Delete Account</DialogTitle>
        <DialogContent>
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="body2" fontWeight="bold">
              This action cannot be undone!
            </Typography>
          </Alert>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Deleting your account will permanently remove:
          </Typography>
          <List dense>
            <ListItem>
              <ListItemText primary="• Your profile information" />
            </ListItem>
            <ListItem>
              <ListItemText primary="• All your prediction history" />
            </ListItem>
            <ListItem>
              <ListItemText primary="• Account settings and preferences" />
            </ListItem>
          </List>
          <Typography variant="body2" color="textSecondary">
            Consider exporting your data before deletion if you want to keep a copy.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDeleteDialog(false)}>Cancel</Button>
          <Button
            onClick={handleDeleteAccount}
            variant="contained"
            color="error"
            disabled={loading}
          >
            {loading ? 'Deleting...' : 'Delete My Account'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ProfilePage;
