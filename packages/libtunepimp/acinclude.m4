dnl @synopsis AC_CHECK_TAGLIB(version, action-if, action-if-not)
dnl
dnl @summary check for taglib of sufficient version by looking at taglib-config
dnl
dnl Defines and exports TAGLIB_LIBS, TAGLIB_CFLAGS. See taglib-config
dnl man page.
dnl
dnl @category InstalledPackages
dnl @author Akos Maroy <darkeye@tyrell.hu>
dnl @version 2005-09-20
dnl @license AllPermissive

AC_DEFUN([AC_CHECK_TAGLIB], [
  succeeded=no

  if test -z "$TAGLIB_CONFIG"; then
    AC_PATH_PROG(TAGLIB_CONFIG, taglib-config, no)
  fi

  if test "$TAGLIB_CONFIG" = "no" ; then
    echo "*** The taglib-config script could not be found. Make sure it is"
    echo "*** in your path, and that taglib is properly installed."
    echo "*** Or see http://developer.kde.org/~wheeler/taglib.html"
  else
    TAGLIB_VERSION=`$TAGLIB_CONFIG --version`
    AC_MSG_CHECKING(for taglib >= $1)
        VERSION_CHECK=`expr $TAGLIB_VERSION \>\= $1`
        if test "$VERSION_CHECK" = "1" ; then
            AC_MSG_RESULT(yes)
            succeeded=yes

            AC_MSG_CHECKING(TAGLIB_CFLAGS)
            TAGLIB_CFLAGS=`$TAGLIB_CONFIG --cflags`
            AC_MSG_RESULT($TAGLIB_CFLAGS)

            AC_MSG_CHECKING(TAGLIB_LIBS)
            TAGLIB_LIBS=`$TAGLIB_CONFIG --libs`
            AC_MSG_RESULT($TAGLIB_LIBS)
        else
            TAGLIB_CFLAGS=""
            TAGLIB_LIBS=""
            ## If we have a custom action on failure, don't print errors, but
            ## do set a variable so people can do so.
            ifelse([$3], ,echo "can't find taglib >= $1",)
        fi

        AC_SUBST(TAGLIB_CFLAGS)
        AC_SUBST(TAGLIB_LIBS)
  fi

  if test $succeeded = yes; then
     ifelse([$2], , :, [$2])
  else
     ifelse([$3], , AC_MSG_ERROR([Library requirements (taglib) not met.]), [$3])
  fi
])
dnl as-ac-expand.m4 0.1.0
dnl autostars m4 macro for expanding directories using configure's prefix
dnl thomas@apestaart.org 

dnl AS_AC_EXPAND(VAR, CONFIGURE_VAR)
dnl
dnl example
dnl AS_AC_EXPAND(SYSCONFDIR, $sysconfdir)
dnl will set SYSCONFDIR to /usr/local/etc if prefix=/usr/local

AC_DEFUN([AS_AC_EXPAND],
[
  EXP_VAR=[$1]
  FROM_VAR=[$2]

  dnl first expand prefix and exec_prefix if necessary
  prefix_save=$prefix
  exec_prefix_save=$exec_prefix

  dnl if no prefix given, then use /usr/local, the default prefix
  if test "x$prefix" = "xNONE"; then
    prefix=$ac_default_prefix
  fi
  dnl if no exec_prefix given, then use prefix
  if test "x$exec_prefix" = "xNONE"; then
    exec_prefix=$prefix
  fi

  full_var="$FROM_VAR"
  dnl loop until it doesn't change anymore
  while true; do
    new_full_var="`eval echo $full_var`"
    if test "x$new_full_var"="x$full_var"; then break; fi
    full_var=$new_full_var
  done

  dnl clean up
  full_var=$new_full_var
  AC_SUBST([$1], "$full_var")

  dnl restore prefix and exec_prefix
  prefix=$prefix_save
  exec_prefix=$exec_prefix_save
])

