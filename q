Help on norm_gen in scipy.stats object:

sscciippyy..ssttaattss..nnoorrmm = class norm_gen(rv_continuous)
 |  A normal continuous random variable.
 |  
 |  The location (loc) keyword specifies the mean.
 |  The scale (scale) keyword specifies the standard deviation.
 |  
 |  %(before_notes)s
 |  
 |  Notes
 |  -----
 |  The probability density function for `norm` is::
 |  
 |      norm.pdf(x) = exp(-x**2/2)/sqrt(2*pi)
 |  
 |  %(example)s
 |  
 |  Method resolution order:
 |      norm_gen
 |      rv_continuous
 |      rv_generic
 |      builtins.object
 |  
 |  Methods defined here:
 |  
 |  ffiitt(self, data, **kwds)
 |      Return MLEs for shape, location, and scale parameters from data.
 |      
 |      MLE stands for Maximum Likelihood Estimate.  Starting estimates for
 |      the fit are given by input arguments; for any arguments not provided
 |      with starting estimates, ``self._fitstart(data)`` is called to generate
 |      such.
 |      
 |      One can hold some parameters fixed to specific values by passing in
 |      keyword arguments ``f0``, ``f1``, ..., ``fn`` (for shape parameters)
 |      and ``floc`` and ``fscale`` (for location and scale parameters,
 |      respectively).
 |      
 |      Parameters
 |      ----------
 |      data : array_like
 |          Data to use in calculating the MLEs.
 |      args : floats, optional
 |          Starting value(s) for any shape-characterizing arguments (those not
 |          provided will be determined by a call to ``_fitstart(data)``).
 |          No default value.
 |      kwds : floats, optional
 |          Starting values for the location and scale parameters; no default.
 |          Special keyword arguments are recognized as holding certain
 |          parameters fixed:
 |      
 |          f0...fn : hold respective shape parameters fixed.
 |      
 |          floc : hold location parameter fixed to specified value.
 |      
 |          fscale : hold scale parameter fixed to specified value.
 |      
 |          optimizer : The optimizer to use.  The optimizer must take func,
 |                      and starting position as the first two arguments,
 |                      plus args (for extra arguments to pass to the
 |                      function to be optimized) and disp=0 to suppress
 |                      output as keyword arguments.
 |      
 |      Returns
 |      -------
 |      shape, loc, scale : tuple of floats
 |          MLEs for any shape statistics, followed by those for location and
 |          scale.
 |      
 |      Notes
 |      -----
 |      This fit is computed by maximizing a log-likelihood function, with
 |      penalty applied for samples outside of range of the distribution. The
 |      returned answer is not guaranteed to be the globally optimal MLE, it
 |      may only be locally optimal, or the optimization may fail altogether.
 |      
 |      This function (norm_gen.fit) uses explicit formulas for the maximum
 |      likelihood estimation of the parameters, so the `optimizer` argument
 |      is ignored.
 |  
 |  ----------------------------------------------------------------------
 |  Methods inherited from rv_continuous:
 |  
 |  ____ccaallll____(self, *args, **kwds)
 |  
 |  ____iinniitt____(self, momtype=1, a=None, b=None, xtol=1e-14, badvalue=None, name=None, longname=None, shapes=None, extradoc=None)
 |  
 |  ccddff(self, x, *args, **kwds)
 |      Cumulative distribution function of the given RV.
 |      
 |      Parameters
 |      ----------
 |      x : array_like
 |          quantiles
 |      arg1, arg2, arg3,... : array_like
 |          The shape parameter(s) for the distribution (see docstring of the
 |          instance object for more information)
 |      loc : array_like, optional
 |          location parameter (default=0)
 |      scale : array_like, optional
 |          scale parameter (default=1)
 |      
 |      Returns
 |      -------
 |      cdf : ndarray
 |          Cumulative distribution function evaluated at `x`
 |  
 |  eennttrrooppyy(self, *args, **kwds)
 |      Differential entropy of the RV.
 |      
 |      Parameters
 |      ----------
 |      arg1, arg2, arg3,... : array_like
 |          The shape parameter(s) for the distribution (see docstring of the
 |          instance object for more information).
 |      loc : array_like, optional
 |          Location parameter (default=0).
 |      scale : array_like, optional
 |          Scale parameter (default=1).
 |  
 |  eesstt__lloocc__ssccaallee(*args, **kwds)
 |      `est_loc_scale` is deprecated!
 |      
 |      This function is deprecated, use self.fit_loc_scale(data) instead.
 |  
 |  eexxppeecctt(self, func=None, args=(), loc=0, scale=1, lb=None, ub=None, conditional=False, **kwds)
 |      Calculate expected value of a function with respect to the distribution
 |      
 |      The expected value of a function ``f(x)`` with respect to a
 |      distribution ``dist`` is defined as::
 |      
 |                  ubound
 |          E[x] = Integral(f(x) * dist.pdf(x))
 |                  lbound
 |      
 |      Parameters
 |      ----------
 |      func : callable, optional
 |          Function for which integral is calculated. Takes only one argument.
 |          The default is the identity mapping f(x) = x.
 |      args : tuple, optional
 |          Argument (parameters) of the distribution.
 |      lb, ub : scalar, optional
 |          Lower and upper bound for integration. default is set to the support
 |          of the distribution.
 |      conditional : bool, optional
 |          If True, the integral is corrected by the conditional probability
 |          of the integration interval.  The return value is the expectation
 |          of the function, conditional on being in the given interval.
 |          Default is False.
 |      
 |      Additional keyword arguments are passed to the integration routine.
 |      
 |      Returns
 |      -------
 |      expect : float
 |          The calculated expected value.
 |      
 |      Notes
 |      -----
 |      The integration behavior of this function is inherited from
 |      `integrate.quad`.
 |  
 |  ffiitt__lloocc__ssccaallee(self, data, *args)
 |      Estimate loc and scale parameters from data using 1st and 2nd moments.
 |      
 |      Parameters
 |      ----------
 |      data : array_like
 |          Data to fit.
 |      arg1, arg2, arg3,... : array_like
 |          The shape parameter(s) for the distribution (see docstring of the
 |          instance object for more information).
 |      
 |      Returns
 |      -------
 |      Lhat : float
 |          Estimated location parameter for the data.
 |      Shat : float
 |          Estimated scale parameter for the data.
 |  
 |  ffrreeeezzee(self, *args, **kwds)
 |      Freeze the distribution for the given arguments.
 |      
 |      Parameters
 |      ----------
 |      arg1, arg2, arg3,... : array_like
 |          The shape parameter(s) for the distribution.  Should include all
 |          the non-optional arguments, may include ``loc`` and ``scale``.
 |      
 |      Returns
 |      -------
 |      rv_frozen : rv_frozen instance
 |          The frozen distribution.
 |  
 |  iissff(self, q, *args, **kwds)
 |      Inverse survival function at q of the given RV.
 |      
 |      Parameters
 |      ----------
 |      q : array_like
 |          upper tail probability
 |      arg1, arg2, arg3,... : array_like
 |          The shape parameter(s) for the distribution (see docstring of the
 |          instance object for more information)
 |      loc : array_like, optional
 |          location parameter (default=0)
 |      scale : array_like, optional
 |          scale parameter (default=1)
 |      
 |      Returns
 |      -------
 |      x : ndarray or scalar
 |          Quantile corresponding to the upper tail probability q.
 |  
 |  llooggccddff(self, x, *args, **kwds)
 |      Log of the cumulative distribution function at x of the given RV.
 |      
 |      Parameters
 |      ----------
 |      x : array_like
 |          quantiles
 |      arg1, arg2, arg3,... : array_like
 |          The shape parameter(s) for the distribution (see docstring of the
 |          instance object for more information)
 |      loc : array_like, optional
 |          location parameter (default=0)
 |      scale : array_like, optional
 |          scale parameter (default=1)
 |      
 |      Returns
 |      -------
 |      logcdf : array_like
 |          Log of the cumulative distribution function evaluated at x
 |  
 |  llooggppddff(self, x, *args, **kwds)
 |      Log of the probability density function at x of the given RV.
 |      
 |      This uses a more numerically accurate calculation if available.
 |      
 |      Parameters
 |      ----------
 |      x : array_like
 |          quantiles
 |      arg1, arg2, arg3,... : array_like
 |          The shape parameter(s) for the distribution (see docstring of the
 |          instance object for more information)
 |      loc : array_like, optional
 |          location parameter (default=0)
 |      scale : array_like, optional
 |          scale parameter (default=1)
 |      
 |      Returns
 |      -------
 |      logpdf : array_like
 |          Log of the probability density function evaluated at x
 |  
 |  llooggssff(self, x, *args, **kwds)
 |      Log of the survival function of the given RV.
 |      
 |      Returns the log of the "survival function," defined as (1 - `cdf`),
 |      evaluated at `x`.
 |      
 |      Parameters
 |      ----------
 |      x : array_like
 |          quantiles
 |      arg1, arg2, arg3,... : array_like
 |          The shape parameter(s) for the distribution (see docstring of the
 |          instance object for more information)
 |      loc : array_like, optional
 |          location parameter (default=0)
 |      scale : array_like, optional
 |          scale parameter (default=1)
 |      
 |      Returns
 |      -------
 |      logsf : ndarray
 |          Log of the survival function evaluated at `x`.
 |  
 |  mmoommeenntt(self, n, *args, **kwds)
 |      n'th order non-central moment of distribution.
 |      
 |      Parameters
 |      ----------
 |      n : int, n>=1
 |          Order of moment.
 |      arg1, arg2, arg3,... : float
 |          The shape parameter(s) for the distribution (see docstring of the
 |          instance object for more information).
 |      kwds : keyword arguments, optional
 |          These can include "loc" and "scale", as well as other keyword
 |          arguments relevant for a given distribution.
 |  
 |  nnnnllff(self, theta, x)
 |      Return negative loglikelihood function
 |      
 |      Notes
 |      -----
 |      This is ``-sum(log pdf(x, theta), axis=0)`` where theta are the
 |      parameters (including loc and scale).
 |  
 |  ppddff(self, x, *args, **kwds)
 |      Probability density function at x of the given RV.
 |      
 |      Parameters
 |      ----------
 |      x : array_like
 |          quantiles
 |      arg1, arg2, arg3,... : array_like
 |          The shape parameter(s) for the distribution (see docstring of the
 |          instance object for more information)
 |      loc : array_like, optional
 |          location parameter (default=0)
 |      scale : array_like, optional
 |          scale parameter (default=1)
 |      
 |      Returns
 |      -------
 |      pdf : ndarray
 |          Probability density function evaluated at x
 |  
 |  ppppff(self, q, *args, **kwds)
 |      Percent point function (inverse of cdf) at q of the given RV.
 |      
 |      Parameters
 |      ----------
 |      q : array_like
 |          lower tail probability
 |      arg1, arg2, arg3,... : array_like
 |          The shape parameter(s) for the distribution (see docstring of the
 |          instance object for more information)
 |      loc : array_like, optional
 |          location parameter (default=0)
 |      scale : array_like, optional
 |          scale parameter (default=1)
 |      
 |      Returns
 |      -------
 |      x : array_like
 |          quantile corresponding to the lower tail probability q.
 |  
 |  ssff(self, x, *args, **kwds)
 |      Survival function (1-cdf) at x of the given RV.
 |      
 |      Parameters
 |      ----------
 |      x : array_like
 |          quantiles
 |      arg1, arg2, arg3,... : array_like
 |          The shape parameter(s) for the distribution (see docstring of the
 |          instance object for more information)
 |      loc : array_like, optional
 |          location parameter (default=0)
 |      scale : array_like, optional
 |          scale parameter (default=1)
 |      
 |      Returns
 |      -------
 |      sf : array_like
 |          Survival function evaluated at x
 |  
 |  ssttaattss(self, *args, **kwds)
 |      Some statistics of the given RV
 |      
 |      Parameters
 |      ----------
 |      arg1, arg2, arg3,... : array_like
 |          The shape parameter(s) for the distribution (see docstring of the
 |          instance object for more information)
 |      loc : array_like, optional
 |          location parameter (default=0)
 |      scale : array_like, optional
 |          scale parameter (default=1)
 |      moments : str, optional
 |          composed of letters ['mvsk'] defining which moments to compute:
 |          'm' = mean,
 |          'v' = variance,
 |          's' = (Fisher's) skew,
 |          'k' = (Fisher's) kurtosis.
 |          (default='mv')
 |      
 |      Returns
 |      -------
 |      stats : sequence
 |          of requested moments.
 |  
 |  ----------------------------------------------------------------------
 |  Methods inherited from rv_generic:
 |  
 |  iinntteerrvvaall(self, alpha, *args, **kwds)
 |      Confidence interval with equal areas around the median.
 |      
 |      Parameters
 |      ----------
 |      alpha : array_like of float
 |          Probability that an rv will be drawn from the returned range.
 |          Each value should be in the range [0, 1].
 |      arg1, arg2, ... : array_like
 |          The shape parameter(s) for the distribution (see docstring of the
 |          instance object for more information).
 |      loc : array_like, optional
 |          location parameter, Default is 0.
 |      scale : array_like, optional
 |          scale parameter, Default is 1.
 |      
 |      Returns
 |      -------
 |      a, b : ndarray of float
 |          end-points of range that contain ``100 * alpha %`` of the rv's possible
 |          values.
 |  
 |  mmeeaann(self, *args, **kwds)
 |      Mean of the distribution
 |      
 |      Parameters
 |      ----------
 |      arg1, arg2, arg3,... : array_like
 |          The shape parameter(s) for the distribution (see docstring of the
 |          instance object for more information)
 |      loc : array_like, optional
 |          location parameter (default=0)
 |      scale : array_like, optional
 |          scale parameter (default=1)
 |      
 |      Returns
 |      -------
 |      mean : float
 |          the mean of the distribution
 |  
 |  mmeeddiiaann(self, *args, **kwds)
 |      Median of the distribution.
 |      
 |      Parameters
 |      ----------
 |      arg1, arg2, arg3,... : array_like
 |          The shape parameter(s) for the distribution (see docstring of the
 |          instance object for more information)
 |      loc : array_like, optional
 |          Location parameter, Default is 0.
 |      scale : array_like, optional
 |          Scale parameter, Default is 1.
 |      
 |      Returns
 |      -------
 |      median : float
 |          The median of the distribution.
 |      
 |      See Also
 |      --------
 |      stats.distributions.rv_discrete.ppf
 |          Inverse of the CDF
 |  
 |  rrvvss(self, *args, **kwds)
 |      Random variates of given type.
 |      
 |      Parameters
 |      ----------
 |      arg1, arg2, arg3,... : array_like
 |          The shape parameter(s) for the distribution (see docstring of the
 |          instance object for more information).
 |      loc : array_like, optional
 |          Location parameter (default=0).
 |      scale : array_like, optional
 |          Scale parameter (default=1).
 |      size : int or tuple of ints, optional
 |          Defining number of random variates (default=1).
 |      
 |      Returns
 |      -------
 |      rvs : ndarray or scalar
 |          Random variates of given `size`.
 |  
 |  ssttdd(self, *args, **kwds)
 |      Standard deviation of the distribution.
 |      
 |      Parameters
 |      ----------
 |      arg1, arg2, arg3,... : array_like
 |          The shape parameter(s) for the distribution (see docstring of the
 |          instance object for more information)
 |      loc : array_like, optional
 |          location parameter (default=0)
 |      scale : array_like, optional
 |          scale parameter (default=1)
 |      
 |      Returns
 |      -------
 |      std : float
 |          standard deviation of the distribution
 |  
 |  vvaarr(self, *args, **kwds)
 |      Variance of the distribution
 |      
 |      Parameters
 |      ----------
 |      arg1, arg2, arg3,... : array_like
 |          The shape parameter(s) for the distribution (see docstring of the
 |          instance object for more information)
 |      loc : array_like, optional
 |          location parameter (default=0)
 |      scale : array_like, optional
 |          scale parameter (default=1)
 |      
 |      Returns
 |      -------
 |      var : float
 |          the variance of the distribution
 |  
 |  ----------------------------------------------------------------------
 |  Data descriptors inherited from rv_generic:
 |  
 |  ____ddiicctt____
 |      dictionary for instance variables (if defined)
 |  
 |  ____wweeaakkrreeff____
 |      list of weak references to the object (if defined)
